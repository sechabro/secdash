import random
import json
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()


def generate_fake_visitor_record_for_date():
    """
    Generate a fake visitor record for a given day.
    The timestamp is set to a random time within the provided day.
    """
    # Random offset within the day (in seconds)
    offset_seconds = random.randint(0, 86399)  # 0 to 23h 59m 59s in seconds
    # random_datetime = day_date + timedelta(seconds=offset_seconds)

    record = {
        "timestamp": datetime.now().isoformat(),
        # "timestamp": random_datetime.isoformat(),
        "ip": fake.ipv4_public(),
        "port": random.randint(1024, 65535),
        "device_info": fake.user_agent(),
        "browser_info": fake.user_agent(),
        "is_bot": random.choice([True, False]),
        "geo_info": f"{fake.city()}, {fake.state()}, {fake.country()}",
        "ipdb": {
            "data": {
                "ipAddress": fake.ipv4_public(),
                "isPublic": True,
                "ipVersion": 4,
                "isWhitelisted": None,
                "abuseConfidenceScore": random.randint(0, 100),
                "countryCode": fake.country_code(),
                "usageType": random.choice(["Commercial", "Residential"]),
                "isp": fake.company(),
                "domain": fake.domain_name(),
                "hostnames": [fake.domain_word() + ".com" for _ in range(random.randint(1, 3))],
                "isTor": random.choice([True, False]),
                "totalReports": random.randint(0, 50),
                "numDistinctUsers": random.randint(0, 10),
                "lastReportedAt": None if random.choice([True, False]) else fake.iso8601()
            }
        }
    }
    return record


def generate_yearly_visitors(start_date: datetime, days: int = 365):
    """
    Generate fake visitor records for a given number of days starting from `start_date`.
    Each day gets a random number of visits between 20 and 100.
    """
    records = []
    for i in range(days):
        day_date = start_date + timedelta(days=i)
        num_visits = random.randint(20, 100)
        for _ in range(num_visits):
            rec = generate_fake_visitor_record_for_date(day_date)
            records.append(rec)
    return records


if __name__ == "__main__":
    # Set the start date for the simulation.
    start_date = datetime(2024, 1, 1)  # Change as needed
    all_records = generate_yearly_visitors(start_date, days=365)

    # Write the data to a JSON file (or output however you like)
    with open("yearly_visitors.json", "w") as f:
        json.dump(all_records, f, indent=2)

    print(f"Generated {len(all_records)} visitor records for one year.")
