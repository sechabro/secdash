import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

import psutil
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi.concurrency import run_in_threadpool

from crud import get_all_ips, upsert_failed_login_attempt
from database import async_session_maker
from schemas import IoStatLineInMem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
psh = PasswordHasher()

# Datastreams deque & lock
iostats = deque(maxlen=30)
running_ps = deque()
ssh_lines = deque(maxlen=20)
ips = deque()
country_counts = deque()
ps_lock = threading.Lock()
ssh_lock = threading.Lock()
ips_lock = threading.Lock()

'''
####### SITE USER MONITORING FUTURE USE #############
async def locale_formatting(client_ip: str) -> str:
    geo_info = db_reader.city(client_ip) # <-- need to install geoip2
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
'''


def established_connections():
    excluded_cmds = {"rapportd", "identitys", "corespeec", "PowerChim"}

    cmd = "lsof -i -P -n | awk '/ESTABLISHED/ && $9 ~ /->/ {split($9, addr, \"->\"); print $1 \",\" $2 \",\" $3 \",\" $4 \",\" $5 \",\" $6 \",\" $7 \",\" $8 \",\" addr[2]}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if not result.stdout:
        return []

    return [
        conn for conn in [
            dict(zip(
                ["cmd", "pid", "user", "fd", "type",
                 "device", "size/off", "node", "address"],
                line.split(",")
            ))
            for line in result.stdout.strip().split("\n") if line
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

# DRAGON [2025-05-27]: stream_delivery() has mutated into an
# overloaded multi-purpose stream processor responsible for sorting,
# filtering, grouping, pagination, and SSE serialization for any
# arbitrary data type. It needs serious breaking up. But that will
# require a serious refactor of all SSE and perhaps even dataclass
# schemas. This comes after MVP deployment. Until then: leave it
# alone, and no more integrations with it.


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
                columns = ["timestamp", "pid", "ppid", "user",
                           "cpu_pct", "stat", "start", "time", "command"]
                fields = line.decode().strip().split(",")

                # pad fields to full length if command value is missing
                fields += ["n/a"] * (len(columns) - len(fields))
                ps_deque_swap.append(dict(zip(columns, fields)))

    except Exception as e:
        logger.info(f' EXCEPTION: {e}')
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
            (date, time, user, nice, sys, iowait, steal,
             idle) = line.decode().strip().split(",")
            iostats.append(
                IoStatLineInMem(
                    date=date,
                    time=time,
                    user=float(user),
                    nice=float(nice),
                    system=float(sys),
                    iowait=float(iowait),
                    steal=float(steal),
                    idle=float(idle)
                )
            )
    except Exception as e:
        logger.error(f' EXCEPTION: {e}')
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


async def ip_stream_manager():
    global ips, country_counts
    old_snapshot = []
    logger.info(f' IP info stream starting.')
    async with async_session_maker() as session:
        while True:
            ips_rows = await get_all_ips(session=session)
            temp_counts = defaultdict(int)
            new_snapshot = [asdict(row) for row in ips_rows]

            for row in new_snapshot:
                country = row.get("country")
                if country == "HK" or country == "TW":
                    temp_counts["CN"] += 1
                else:
                    temp_counts[country] += 1

            if new_snapshot != old_snapshot:
                with ips_lock:
                    ips.clear()
                    ips.extend(ips_rows)
                    country_counts = dict(temp_counts)
                old_snapshot = new_snapshot
            else:
                pass
            await asyncio.sleep(30)


async def ip_stream_delivery():
    global ips, country_counts
    old_snapshot = []
    while True:
        await asyncio.sleep(2)
        with ips_lock:
            new_snapshot = [asdict(ip) for ip in ips]
            counts_snapshot = country_counts
        if new_snapshot != old_snapshot:
            yield f"data: {json.dumps({'ips': new_snapshot, 'country_counts': counts_snapshot})}\n\n"
            old_snapshot = new_snapshot
        else:
            pass


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
