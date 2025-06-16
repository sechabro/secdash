from subprocess import CalledProcessError
from unittest.mock import patch

from ipset import ipset_calls


def test_ipset_calls_banned_success():
    with patch("ipset.subprocess.run") as mock_run:
        mock_run.return_value = None  # simulate successful run

        result = ipset_calls("192.0.2.1", "banned")

        assert result["status"] == "Banned"
        assert result["ip"] == "192.0.2.1"
        mock_run.assert_called_once_with(
            ["ipset", "add", "blacklist", "192.0.2.1"], check=True)

# Test 2: Successful IP restore (action="active")


def test_ipset_calls_active_success():
    with patch("ipset.subprocess.run") as mock_run:
        mock_run.return_value = None

        result = ipset_calls("198.51.100.5", "active")

        assert result["status"] == "Active"
        assert result["ip"] == "198.51.100.5"
        mock_run.assert_called_once_with(
            ["ipset", "del", "blacklist", "198.51.100.5"], check=True)

# Test 3: Invalid action


def test_ipset_calls_invalid_action():
    result = ipset_calls("203.0.113.9", "freeze")
    assert result["status"] == "failure"
    assert "Invalid action" in result["error"]

# Test 4: subprocess.run raises CalledProcessError


def test_ipset_calls_subprocess_error():
    with patch("ipset.subprocess.run") as mock_run:
        mock_run.side_effect = CalledProcessError(
            1, ["ipset", "add", "blacklist", "203.0.113.9"])

        result = ipset_calls("203.0.113.9", "banned")

        assert result["status"] == "failure"
        assert "error" in result
