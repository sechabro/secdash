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
from h11 import Request

from crud import alerts, get_all_ips, upsert_failed_login_attempt
from database import async_session_maker
from schemas import IoStatLineInMem
from stream_manager import StreamManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
psh = PasswordHasher()

# Datastreams deque & lock
# ssh_lines = deque(maxlen=20)
ips = deque()
country_counts = deque()
ssh_lock = threading.Lock()
ips_lock = threading.Lock()


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
###############################################################################
###############################################################################

# DRAGON [2025-06-22]: Holdovers from the evil `stream_delivery()` monolith.
# Leave for now, will be valuable to integrate into StreamManager.

'''def get_field_value(item: Any, field: str):
    """Universal accessor for both dicts and dataclasses."""
    if isinstance(item, dict):
        return item.get(field, None)
    elif is_dataclass(item):
        return getattr(item, field, None)
    return None


def paginate(page: int, limit: int, snapshot: list) -> tuple:
    total_items = len(snapshot)
    start = (page - 1) * limit
    end = start + limit
    new_snapshot = snapshot[start:end]
    return (new_snapshot, total_items)'''


# closure implementation to allow for partial
# arg construction on instantiation. Great little solution.
def group_by_keys(outer_key: str, inner_key: str):
    def grouped_items(items: list[dict]) -> list:
        return_dict = {}
        for item in items:
            group = item.get(outer_key)
            group_value = item.get(inner_key)
            if not return_dict.get(group):
                return_dict[group] = {}
            if not return_dict[group].get(group_value):
                return_dict[group][group_value] = []
            return_dict[group][group_value].append(item)
        return [{group: data} for group, data in return_dict.items()]
    return grouped_items


###############################################################################
#### SYSTEM PROCESS ###########################################################
################# METRICS #####################################################
####################### STREAM ################################################


async def ps_stream(ps_manager: StreamManager):
    processes = await ps_manager.run_script()

    try:
        logger.info(f' Process stream starting.')
        ps_deque_swap = deque()
        async for line in processes.stdout:
            line_strip = line.decode().strip()
            if line_strip == "END":
                if ps_deque_swap:
                    # logger.info(
                    #    f"⏱️ Process lines parsed: {len(ps_deque_swap)}")
                    with ps_manager.lock:
                        ps_manager.deque.clear()
                        ps_manager.deque.extend(ps_deque_swap)
                    ps_deque_swap.clear()
            else:
                columns = ["timestamp", "pid", "ppid", "user",
                           "cpu_pct", "stat", "start", "time", "command"]
                fields = line.decode().strip().split(",")

                # pad fields to full length if command value is missing from line
                fields += ["n/a"] * (len(columns) - len(fields))
                ps_deque_swap.append(dict(zip(columns, fields)))

    except Exception as e:
        logger.info(f' EXCEPTION: {e}')

################################################################
#### IOSTAT ####################################################
######### METRICS ##############################################
############### STREAM #########################################


async def io_stream(iostat_manager: StreamManager):
    iostat_data = await iostat_manager.run_script()
    try:
        logger.info(f' Iostat stream starting.')
        async for line in iostat_data.stdout:
            (date, time, user, nice, sys, iowait, steal,
             idle) = line.decode().strip().split(",")
            iostat_manager.deque.append(
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

################################################################
##### FAILED ###################################################
########## SSH #################################################
############ LOGIN #############################################
################ STREAM ########################################


async def ssh_watch(ssh_manager: StreamManager):
    ssh_data = await ssh_manager.run_script()
    try:
        logger.info(f' Ssh watch starting.')
        new_ssh_lines = deque()
        listener_note = False
        async for line in ssh_data.stdout:
            decode = line.decode().strip()
            if decode == "END":
                old_snapshot = list(ssh_manager.deque)
                new_snapshot = list(new_ssh_lines)
                if new_snapshot != old_snapshot:
                    new_crud_lines = [
                        line for line in new_snapshot if line not in old_snapshot]
                    logger.info(
                        f' 🌐 {len(new_crud_lines)} new ssh attempt(s) detected.')
                    await upsert_failed_login_attempt(batch=new_crud_lines)
                    with ssh_manager.lock:
                        ssh_manager.deque.clear()
                        ssh_manager.deque.extend(new_ssh_lines)
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


################################################################
##### IP #######################################################
###### INFO ####################################################
######### DELIVERY #############################################
################ STREAM ########################################

# DRAGON [2025-06-22]: Integrate via StreamManager class.
# This system is somewhat different from what StreamManager handles.
# It may be necessary to create a custom class for this, that inherits
# StreamManager functionality.

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

###### MISCELLANEOUS ##################


async def host_info_async() -> dict:
    def host_info():
        uptime = time.time() - psutil.boot_time()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
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
