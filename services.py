import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from schemas import VisitorInMem

load_dotenv()

ipdb_key = os.getenv("IPDB")
openai_key = os.getenv("OPENKEY001")
# org = os.getenv("OPENORG")  # optional, for organization arg if needed
client = OpenAI(api_key=openai_key)


async def analyze_visitor(visitor: VisitorInMem):
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
        raise HTTPException(status_code=500, detail=str(e))


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

    return response.json()
