import asyncio
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ipset_calls(ip: str, action: str | None = "blacklist") -> dict:
    if action == "blacklist":
        f_string = f"ipset add blacklist {ip}"
    elif action == "whitelist":
        f_string = f"ipset del blacklist {ip}"
    else:
        return {"status": "failure", "error": f"Invalid action: {action}"}
    try:
        cmd = [
            "ssh",
            "secdash-vps",
            f_string
        ]
        subprocess.run(cmd, check=True)

        logger.info(f" {action.capitalize()}ed IP: {ip}")
        return {"status": "success", "ip": ip}

    except subprocess.CalledProcessError as e:
        logger.info(f" Error {action.capitalize()}ing IP {ip}: {e}")
        return {"status": "failure", "error": str(e)}


# if __name__ == "__main__":
#    banhammer = asyncio.run(ipset_calls("203.0.113.123", "blacklist"))
#    print(banhammer)
