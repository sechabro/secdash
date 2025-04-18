import json
import subprocess
from functools import reduce
import smtplib
from geoip2 import webservice, database, errors
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import Request, HTTPException, FastAPI, APIRouter
from fastapi.concurrency import run_in_threadpool
from datetime import datetime
from user_agents import parse
from schemas import Visitor, IOStatLine
from data_generator import generate_fake_visitor_record_for_date
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
import os
import psutil
import time
import httpx
import asyncio
from collections import deque
from sqlmodel import Session
from crud import visitor_info_post, get_user_by_email
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
psh = PasswordHasher()

# DB Reader
db_reader = database.Reader('./GeoLite2-City.mmdb')
IPDB = str(os.getenv('IPDB', default=None))

# Datastreams
iostats = deque(maxlen=30)
running_ps = deque(maxlen=45)


def block_ip(ip):
    '''Install ipset: sudo apt-get install ipset -y
    sudo ipset create blacklist hash:ip
    By default, ipset rules won't persist across reboots. To make the blacklist persistent:
    sudo ipset save > /etc/ipset.rules
    Ensure that ipset restores the rules after a reboot: sudo nano /etc/rc.local
    Add this line before exit 0: ipset restore < /etc/ipset.rules
    command to list out ipset info for your blacklist: sudo ipset list blacklist'''

    # Adds an IP to ipset's blacklist.
    try:
        # Add IP to the blacklist set
        subprocess.run(["sudo", "ipset", "add", "blacklist", ip], check=True)

        print(f"Blocked IP: {ip} using ipset.")
        return {"status": "success", "action": "block_ip", "ip": ip}

    except subprocess.CalledProcessError as e:
        print(f"Error blocking IP {ip}: {e}")
        return {"status": "failure", "error": str(e)}


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


async def stream_delivery(data_stream: deque):
    old_snapshot = []
    while True:
        await asyncio.sleep(1)
        new_snapshot = list(data_stream)
        if new_snapshot != old_snapshot:
            yield f"data: {json.dumps(new_snapshot)}\n\n"
            old_snapshot = new_snapshot

###############################################################################
#### SYSTEM PROCESS ###########################################################
################# METRICS #####################################################
####################### STREAM ################################################


async def ps_stream(script: str | None = None):
    processes = await run_script(script=script)
    try:
        async for line in processes.stdout:
            line_strip = line.decode().strip()
            if line_strip == "END":
                if running_ps:
                    continue
            else:
                running_ps.append(
                    dict(
                        zip(
                            ["date", "time", "user", "pid", "cpu_pct", "mem_pct", "vsz_kb",
                                "rss_kb", "tty", "stat", "start", "cpu_time", "command"],
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
        async for line in iostat_data.stdout:
            iostats.append(dict(zip(
                ["date", "time", "kbt", "tps", "mbs",
                    "user", "sys", "idle", "load_avg_1m"],
                line.decode().strip().split(",")
            )))
    except KeyboardInterrupt:
        print("Stopping...")
        iostat_data.terminate()

################################################################
################################################################
################################################################


async def visitor_info(request: Request, session: Session) -> dict:
    # Get the visitor's IP address (you might need to adapt this for proxies)
    client_ip = request.client.host
    client_port = request.client.port
    if client_ip in ("127.0.0.1", "::1"):
        # This is FAKE record generation, and temporary for dev and pre-population purposes only.
        fake_info = generate_fake_visitor_record_for_date()
        visitor = Visitor(
            timestamp=fake_info.get("timestamp"),
            ip=fake_info.get("ip"),
            port=str(fake_info.get("port")),
            device_info=fake_info.get("device_info"),
            browser_info=fake_info.get("browser_info"),
            is_bot=fake_info.get("is_bot"),
            geo_info=fake_info.get("geo_info"),
            ipdb=fake_info.get("ipdb")
        )
        info_post = await visitor_info_post(session=session, item=visitor)
        return info_post.model_dump()

    # Get the timestamp of the request
    timestamp = datetime.now().isoformat()

    # get the user-agent raw string from request headers, and parse it out
    ua_string = dict(request.headers).get("user-agent")
    user_agent = parse(ua_string)
    device_info = f"{user_agent.device.family} {user_agent.device.brand} {user_agent.os.family} {user_agent.os.version_string}"
    browser_info = f"{user_agent.browser.family} {user_agent.browser.version_string}"
    is_bot = user_agent.is_bot

    # geo info try-block
    try:
        geo_info = await locale_formatting(client_ip=client_ip)
    except Exception as e:
        geo_info = str(e)

    ip_info = await ipabuse_check(ip=client_ip)

    visitor = Visitor(timestamp=timestamp, ip=client_ip, port=str(client_port),
                      device_info=device_info, browser_info=browser_info, is_bot=is_bot, geo_info=geo_info, ipdb=ip_info)

    # You can now process this data, store it in the database, etc.
    info_post = await visitor_info_post(db=session, item=visitor)
    return info_post.model_dump()


async def ipabuse_check(ip: str):
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {
        "Key": IPDB,
        "Accept": "application/json"
    }
    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()  # raises an error for bad responses

    return response.json()


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
