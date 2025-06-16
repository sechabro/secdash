import asyncio
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ipset_calls(ip: str, action: str | None = "banned") -> dict:
    if action == "banned":
        f_string = f"ipset add blacklist {ip}"
    elif action == "active":
        f_string = f"ipset del blacklist {ip}"
    else:
        return {"status": "failure", "error": f"Invalid action: {action}"}
    try:
        # local testing only
        # cmd = [
        #    "ssh",
        #    "secdash-vps",
        #    f_string
        # ]
        cmd = f_string.split()
        subprocess.run(cmd, check=True)
        # logger.info(f' ipset bypass local testing')
        status_string = f"{action.capitalize()}"
        logger.info(f" {status_string} IP: {ip}")
        return {"status": status_string, "ip": ip}

    except subprocess.CalledProcessError as e:
        logger.info(
            f"ERROR: IP {ip} Not {action.capitalize()} Successfully: {e}")
        return {"status": "failure", "error": str(e)}


# if __name__ == "__main__":
#    banhammer = asyncio.run(ipset_calls("203.0.113.123", "blacklist"))
#    print(banhammer)
