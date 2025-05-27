import asyncio
import json
import logging
import os
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from functools import reduce
from ipaddress import ip_address
from typing import Any, Callable

import psutil
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from geoip2 import database, errors, webservice
from pympler import asizeof
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session
from user_agents import parse

from crud import (get_user_by_email, get_visitors, shutdown_db_update,
                  upsert_failed_login_attempt, visitor_info_post)
from database import async_session_maker
from schemas import FailedLoginIntel, IoStatLineInMem, Visitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
psh = PasswordHasher()

# DB Reader
db_reader = database.Reader('./GeoLite2-City.mmdb')

# Datastreams
iostats = deque(maxlen=30)
running_ps = deque()
visitors = deque()
ssh_lines = deque(maxlen=20)
ps_lock = threading.Lock()
visitor_lock = threading.Lock()
ssh_lock = threading.Lock()


async def locale_formatting(client_ip: str) -> str:
    geo_info = db_reader.city(client_ip)
    locale_parts = ["city.name",
                    "subdivisions.most_specific.name", "country.name"]
    locale_info = []
    async for part in locale_parts:
        try:
            info = reduce(getattr, part.split("."), geo_info)
            locale_info.append(info)
        except AttributeError:
            locale_info.append("not found")
    return ", ".join(locale_info)


async def established_connections():
    result = await asyncio.create_subprocess_shell(
        cmd="lsof -i -P -n | awk '/ESTABLISHED/ && $9 ~ /->/ {split($9, addr, \"->\"); print $1 \",\" $2 \",\" $3 \",\" $4 \",\" $5 \",\" $6 \",\" $7 \",\" $8 \",\" addr[2]}'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    # returns a tuple of stdout and stderr
    stdout_bytes, stderr_bytes = await result.communicate()
    # Decoding to string and stripping all white space if exists -> "value,value,value,value" format per line
    output = stdout_bytes.decode().strip()
    if not output:
        return []

    excluded_cmds = {"rapportd", "identitys", "corespeec", "PowerChim"}

    return [conn for conn in
            [
                dict(zip(
                    ["cmd", "pid", "user", "fd", "type",
                     "device", "size/off", "node", "address"],
                    line.split(",")
                ))
                # for line in result.stdout.strip().split("\n") if line
                for line in output.split("\n") if line
            ]
            if conn.get("cmd") not in excluded_cmds
            ]

######################### UNIVERSAL BASH SCRIPT RUNNER ########################
# Call this when you need to run a background process, specifically for system
# metrics data streaming.


async def run_script(script: str | None = None):
    return await asyncio.create_subprocess_exec(script,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)


###############################################################################
####################### UNIVERSAL STREAM DELIVERY SERVICE #####################
##################### WITH HELPERS! ###########################################


def get_field_value(item: Any, field: str):
    """Universal accessor for both dicts and dataclasses."""
    if isinstance(item, dict):
        return item.get(field, None)
    elif is_dataclass(item):
        return getattr(item, field, None)
    return None


def serialize(item: Any):
    """Universal serializer for dicts and dataclasses."""
    if is_dataclass(item):
        return asdict(item)
    return item  # assuming it's already a dict


async def stream_delivery(
    data_stream: deque,
    sort: bool | None = False,
    key: str | None = None,
    group: bool | None = False,
    outer_key: str | None = None,
    inner_key: str | None = None,
    filter_field: str | None = None,
    filter_param: str | None = None,
    page: int | None = None,
    limit: int | None = None
):
    old_snapshot = []
    while True:
        await asyncio.sleep(1)
        total_items = None
        new_snapshot = list(data_stream)

        # Sorting
        if sort and key:
            new_snapshot.sort(
                key=lambda item: get_field_value(item, key) or "")

        # Filtering
        if filter_field and filter_param is not None:
            if isinstance(filter_param, str) and filter_param.lower() in ("true", "false"):
                filter_param = filter_param.lower() == "true"

            new_snapshot = [
                item for item in new_snapshot
                if get_field_value(item, filter_field) == filter_param
            ]

        # DRAGON [2025-05-10]: SLAYED. Grouping modularized and decoupled.
        # Grouping
        if group:
            grouping_snapshot = list(data_stream)
            new_snapshot = group_by_keys(
                items=grouping_snapshot, outer_key=outer_key, inner_key=inner_key)

        # Pagination
        if page is not None and limit is not None:
            paginating_snapshot = new_snapshot
            new_snapshot, total_items = paginate(
                page=page, limit=limit, snapshot=paginating_snapshot)

        if new_snapshot != old_snapshot:
            # needed to determine page total for frontend
            is_dc = is_dataclass(new_snapshot[0]) if new_snapshot else False
            serialized = [
                asdict(item) if is_dc else item for item in new_snapshot]
            if total_items:
                yield f"event: meta\ndata: {json.dumps({'total_items': total_items})}\n\n"
            yield f"data: {json.dumps(serialized)}\n\n"
            old_snapshot = new_snapshot


def paginate(page: int, limit: int, snapshot: list) -> tuple:
    total_items = len(snapshot)
    start = (page - 1) * limit
    end = start + limit
    new_snapshot = snapshot[start:end]
    return (new_snapshot, total_items)


def group_by_keys(items: list, outer_key: str, inner_key: str) -> list:
    return_dict = {}
    for item in items:
        group = item.get(outer_key)
        group_value = item.get(inner_key)
        if not return_dict.get(group):
            return_dict.update({group: {}})
        if not return_dict[group].get(group_value):
            return_dict[group][group_value] = []
        return_dict[group][group_value].append(item)
    return [{group: data} for group, data in return_dict.items()]


###############################################################################
#### SYSTEM PROCESS ###########################################################
################# METRICS #####################################################
####################### STREAM ################################################


async def ps_stream(script: str | None = None):
    global running_ps
    processes = await run_script(script=script)

    try:
        logger.info(f' Process stream starting.')
        ps_deque_swap = deque()
        async for line in processes.stdout:
            line_strip = line.decode().strip()
            if line_strip == "END":
                if ps_deque_swap:
                    with ps_lock:
                        running_ps.clear()
                        running_ps.extend(ps_deque_swap)
                    ps_deque_swap.clear()
            else:
                ps_deque_swap.append(
                    dict(
                        zip(
                            ["timestamp", "pid", "ppid", "user", "cpu_pct", "stat",
                                "start", "time", "command"],
                            line.decode().strip().split(",")
                        )
                    )
                )

    except KeyboardInterrupt:
        print("Stopping...")
        processes.terminate()

################################################################
#### IOSTAT ####################################################
######### METRICS ##############################################
############### STREAM #########################################


async def io_stream(script: str | None = None):
    iostat_data = await run_script(script=script)
    try:
        logger.info(f' Iostat stream starting.')
        async for line in iostat_data.stdout:
            (date, time, kbt, tps, mbs, user, sys, idle,
             load) = line.decode().strip().split(",")
            iostats.append(
                IoStatLineInMem(
                    date=date,
                    time=time,
                    kbt=float(kbt),
                    tps=int(tps),
                    throughput_mbs=float(mbs),
                    cpu_user_pct=float(user),
                    cpu_system_pct=float(sys),
                    cpu_idle_pct=float(idle),
                    load_avg_1m=float(load)
                )
            )
    except KeyboardInterrupt:
        print("Stopping...")
        iostat_data.terminate()

################################################################
##### FAILED ###################################################
########## SSH #################################################
############ LOGIN #############################################
################ STREAM ########################################


async def ssh_stream(script: str | None = None):
    global ssh_lines

    ssh_data = await run_script(script=script)
    try:
        logger.info(f' Ssh stream starting.')
        new_ssh_lines = deque()
        listener_note = False
        async for line in ssh_data.stdout:
            decode = line.decode().strip()
            if decode == "END":
                old_snapshot = list(ssh_lines)
                new_snapshot = list(new_ssh_lines)
                if new_snapshot != old_snapshot:
                    new_crud_lines = [
                        line for line in new_snapshot if line not in old_snapshot]
                    logger.info(
                        f' 🌐 {len(new_crud_lines)} new ssh attempt(s) detected.')
                    await upsert_failed_login_attempt(batch=new_crud_lines)
                    with ssh_lock:
                        ssh_lines.clear()
                        ssh_lines.extend(new_ssh_lines)
                    listener_note = True
                elif listener_note:
                    logger.info(" Listening for new ssh attempts... 📡")
                    listener_note = False
                new_ssh_lines.clear()
            else:
                decode_split = [val.strip()
                                for val in decode.split(",", maxsplit=3)]
                if len(decode_split) == 4:
                    new_ssh_lines.append(decode_split)

    except KeyboardInterrupt:
        print("Stopping SSH Monitor...")
        ssh_data.terminate()

####### VISITOR ################################################
######## ACTIVITY ##############################################
########## GENERATION ##########################################
# This data is designed to mimic the logging in, logging out,
# idle time, active time, and session activity of users to a site
# that SecDash is tasked with monitoring. For now, this data is
# generated for demo purposes. Abuse IPDB data is also generated,
# to avoid potential issues with over-calling their api in short-
# timespans.


async def visitor_stream(visitor_list: list | None = None):
    global visitors
    try:
        visitor_deque_swap = deque()
        async for visitor in visitor_list:
            visitor_deque_swap.append(visitor)
            if visitor_deque_swap:
                with visitor_lock:
                    visitors.clear()
                    visitors.extend(visitor_deque_swap)
                visitor_deque_swap.clear()
    except KeyboardInterrupt:
        print("Stopping...")


async def visitor_activity_gen():
    global visitors
    try:
        async with async_session_maker() as session:
            db_visitors = await get_visitors(session)
            # logger.info(f' VISITORS: {db_visitors}\n\n')
            active_visitors = [v for v in db_visitors if v.is_active]
            inactive_visitors = [v for v in db_visitors if not v.is_active]

            while True:
                # Mutate the visitors
                # Example: activate some, idle some, log out some
                to_activate = random.sample(inactive_visitors, k=min(
                    len(inactive_visitors), random.randint(1, 5)))
                for visitor in to_activate:
                    visitor.is_active = True
                    visitor.last_active = datetime.now().isoformat()
                    visitor.time_idle = 0
                    active_visitors.append(visitor)
                    inactive_visitors.remove(visitor)

                for visitor in active_visitors:
                    if random.random() < 0.7:
                        visitor.last_active = datetime.now().isoformat()
                        visitor.time_idle = 0
                    else:
                        visitor.time_idle += random.randint(10, 40)

                to_logout = random.sample(active_visitors, k=min(
                    len(active_visitors), max(1, len(active_visitors) // 20)))
                for visitor in to_logout:
                    visitor.is_active = False
                    visitor.time_idle = 0
                    inactive_visitors.append(visitor)
                    active_visitors.remove(visitor)

                # Push updated list into the global deque
                updated_visitors = active_visitors + inactive_visitors
                with visitor_lock:
                    visitors.clear()
                    visitors.extend([v for v in updated_visitors])
                '''vis_list = list(visitors)
                byte_syze = asizeof.asizeof(vis_list)
                in_mb = byte_syze / (1024 * 1024)
                logger.info(
                    f' Total memory used by Visitor List: {byte_syze} bytes ({in_mb:.2f} MB)"')
                # Memory used per key across all visitors
                field_memory = defaultdict(int)

                # Sum up memory usage of each field individually
                for visitor in vis_list:
                    for field in fields(visitor):
                        key = field.name
                        value = getattr(visitor, key)
                        field_memory[key] += asizeof.asizeof(value)

                # Sort and display results
                sorted_fields = sorted(field_memory.items(),
                                       key=lambda x: x[1], reverse=True)

                logger.info("Memory usage by field (descending):")
                for key, size in sorted_fields:
                    logger.info(f"{key:20}: {size / 1024:.2f} KB")'''

                await asyncio.sleep(random.randint(20, 40))
    except Exception as e:
        logger.exception(f' EXCEPTION: {e}')


async def persist_visitors() -> bool:
    async with async_session_maker() as session:
        with visitor_lock:
            updates = list(visitors)
            shutdown_update = await shutdown_db_update(session=session, visitor_list=updates)
            return shutdown_update


async def host_info_async() -> dict:
    def host_info():
        uptime = time.time() - psutil.boot_time()
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": int(uptime),
            "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        }
    return await run_in_threadpool(host_info)


async def password_verify(password: str | None = None,
                          hashed: str | None = None) -> bool:
    try:
        return await run_in_threadpool(psh.verify, hash=hashed, password=password)
    except VerificationError:
        logger.error(
            f' Password verification error at {datetime.now().isoformat()}: {VerificationError.args[0]}.')
        return False


async def password_hasher(password: str | None = None) -> str:
    return await run_in_threadpool(psh.hash, password=password)
