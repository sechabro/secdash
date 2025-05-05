import random
import asyncio
from datetime import datetime, timedelta
from faker import Faker

from database import async_session_maker
from schemas import Visitor
from crud import visitor_info_post  # wherever your visitor_info_post is

fake = Faker()


async def generate_fake_visitors(total: int = 1000):
    usernames = []

    async with async_session_maker() as session:
        for _ in range(total):
            username = fake.user_name()
            visitor = Visitor(
                username=username,
                acct_created=fake.date_time_between(
                    start_date='-5y', end_date='now').isoformat(),
                ip=fake.ipv4_public(),
                port=str(random.randint(1024, 65535)),
                device_info=random.choice([
                    "Windows 10 PC",
                    "MacBook Pro (macOS 13)",
                    "Samsung Galaxy S22 (Android 12)",
                    "iPhone 13 Pro (iOS 15)",
                    "Google Pixel 7 (Android 13)",
                    "iPad Air (iOS 16)",
                    "iPhone 16 (iOS 18)"
                ]),
                browser_info=fake.user_agent(),
                is_bot=random.choice([True] + [False] * 7),  # 1/8 bots
                geo_info=f"{fake.city()}, {fake.state()}, {fake.country()}",
                ipdb={
                    "ipAddress": fake.ipv4_public(),
                    "isPublic": True,
                    "ipVersion": 4,
                    "isWhitelisted": None,
                    "abuseConfidenceScore": random.randint(0, 100),
                    "countryCode": fake.country_code(),
                    "usageType": fake.random_element(["Commercial", "Residential", "Data Center"]),
                    "isp": fake.company(),
                    "domain": fake.domain_name(),
                    "hostnames": [fake.domain_name()],
                    "isTor": random.choice([True] + [False]*3),
                    "totalReports": random.randint(0, 200),
                    "numDistinctUsers": random.randint(1, 20),
                    "lastReportedAt": fake.date_time_between(start_date='-10y', end_date='now').isoformat()
                },
                last_active=None,
                time_idle=0,
                is_active=False
            )

            await visitor_info_post(session=session, item=visitor)
            usernames.append(username)

    # Save usernames to a local file
    with open("all_users.py", "w") as f:
        f.write(f"usernames = {usernames}\n")

    print(f"✅ Successfully seeded {total} visitors and saved usernames.")

if __name__ == "__main__":
    asyncio.run(generate_fake_visitors())
