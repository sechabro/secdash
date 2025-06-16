import asyncio
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import false

from schemas import FailedLoginInMem

load_dotenv()

ipdb_key = os.getenv("IPDB")
openai_key = os.getenv("OPENKEY001")
# org = os.getenv("OPENORG")  # optional, for organization arg if needed
client = OpenAI(api_key=openai_key)


'''async def analyze_visitor(visitor: VisitorInMem):
    prompt = f"""
    You are an AI security analyst. Evaluate the following visitor activity and return a JSON object with:
    - "risk_level" (low, medium, or high)
    - "justification"
    - "recommended_action"

    Visitor Details:
    Username: {visitor.username}
    Account Created: {visitor.acct_created}
    IP: {visitor.ip}
    Port: {visitor.port}
    Device Info: {visitor.device_info}
    Browser Info: {visitor.browser_info}
    Is Bot: {visitor.is_bot}
    Geo Info: {visitor.geo_info}
    AbuseIPDB isTor: {visitor.ipdb}
    Last Active: {visitor.last_active}
    Time Idle (seconds): {visitor.time_idle}
    Is Currently Active: {visitor.is_active}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''


async def analyze_ip_address(ip: FailedLoginInMem) -> dict:
    prompt = f"""
    You are an AI security analyst. The following information
    contains details about an IP address's SSH attempts against 
    a private VPS, as well as intel from Abuse IPDB. Evaluate 
    it and return only a valid JSON object matching this schema.

    Example:
    {{
      "ip_address": "{ip.ip}",
      "ip_id": "{ip.ip_id}
      "risk_level": "red",
      "analysis": "...",
      "recommended_action": "ban"
    }}:

    Permitted values per key:
    - "risk_level" one of ["green", "yellow", "orange", "red", "black"]
    - "analysis" (a clear and concise explanation justifying the action)
    - "recommended_action" one of ["monitor", "flag", "review", "suspend", "ban", "autoban"]

    If an IP has an Abuse IPDB confidence score over 90, is a 
    known Tor exit node, or has more than 500 Abuse IPDB reports, it 
    should be considered high risk. Combining two or more of these 
    factors warrants a 'black' risk level. Do not hesitate to 
    assign 'black' when strong indicators of malicious activity are 
    present. Your priority is to protect the server, even at the 
    cost of false positives.

    Adhere to this table for permitted risk_level
    and recommended_action pairs:

    | Risk Level | Allowed Actions           |
    |------------|---------------------------|
    | black      | autoban                   |
    | red        | suspend, ban              |
    | orange     | flag, suspend             |
    | yellow     | review                    |
    | green      | monitor                   |

    Do not include any markdown formatting.

    IP Address Intel:
    IP Address: {ip.ip}
    Abuse IPDB abuseConfidenceScore: {ip.score}
    Abuse IPDB isTor: {ip.is_tor}
    Abuse IPDB totalReports: {ip.total_reports}
    First attempt date: {ip.first_seen}
    Last attempt date: {ip.last_seen}
    Total attempts: {ip.count}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        return {"error": str(e), "ip_info": ip}


# DRAGON [2025-05-23]: scaling issue with asyncio.gather()
# It might be necessary to replace asyncio.gather() if too many
# items are added at once. Consider asyncio.Queue, asyncio.Semaphore.
# Monitor for now.


async def ip_analysis_gathering(ip_info: list[FailedLoginInMem]) -> list[dict]:
    tasks = [analyze_ip_address(ip) for ip in ip_info]
    return await asyncio.gather(*tasks)


async def ipabuse_check(ip: str):
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {
        "Key": ipdb_key,
        "Accept": "application/json"
    }
    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()  # raises an error for bad responses

    return response.json().get("data", {})


'''if __name__ == "__main__":
    test_ip = FailedLoginInMem(
        ip="27.150.182.11",
        score=97,
        is_tor=False,
        total_reports=500,
        count=10,
        first_seen='2025-05-29 00:02:21.713862',
        last_seen='2025-05-29 00:54:59.445423'
    )
    result = asyncio.run(ip_analysis_gathering(ip_info=[test_ip]))
    print(result)'''
