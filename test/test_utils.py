import asyncio
import json
from asyncio import Queue
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from schemas import AlertStatus, AlertType
from utils import (alert_stream_delivery, alerts_queue,
                   established_connections, get_field_value, group_by_keys,
                   host_info_async, io_stream, iostats, paginate, ps_lock,
                   ps_stream, run_script, running_ps, serialize)


def test_established_connections_parses_and_filters_correctly():
    fake_stdout = "\n".join([
        "ssh,1234,user1,fd1,IPv4,dev1,0t0,TCP,192.168.1.2:22",
        "rapportd,5678,user2,fd2,IPv6,dev2,0t0,TCP,10.0.0.5:443",  # should be excluded
        "nginx,9101,user3,fd3,IPv4,dev3,0t0,TCP,203.0.113.42:80"
    ])

    mock_result = Mock()
    mock_result.stdout = fake_stdout

    with patch("utils.subprocess.run", return_value=mock_result):
        connections = established_connections()

    assert isinstance(connections, list)
    assert len(connections) == 2  # rapportd should be excluded
    assert connections[0]["cmd"] == "ssh"
    assert connections[1]["cmd"] == "nginx"
    assert connections[0]["address"] == "192.168.1.2:22"


def test_established_connections_no_stdout():
    fake_stdout = ""

    mock_result = Mock()
    mock_result.stdout = fake_stdout

    with patch("utils.subprocess.run", return_value=mock_result):
        connections = established_connections()

    assert connections == []


@pytest.mark.asyncio
async def test_run_script_executes_and_returns_process():
    mock_process = AsyncMock()
    mock_process.stdout = asyncio.subprocess.PIPE
    mock_process.stderr = asyncio.subprocess.PIPE

    with patch("utils.asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await run_script("test_script.sh")

    mock_exec.assert_called_once_with(
        "test_script.sh", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    assert result.stdout == asyncio.subprocess.PIPE
    assert result.stderr == asyncio.subprocess.PIPE


@pytest.mark.asyncio
async def test_run_script():
    mock_process = AsyncMock()
    mock_process.stdout = asyncio.subprocess.PIPE
    mock_process.stderr = asyncio.subprocess.PIPE

    with patch("utils.asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await run_script("test_script.sh")

    mock_exec.assert_called_once_with(
        "test_script.sh", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    assert result.stdout == asyncio.subprocess.PIPE
    assert result.stderr == asyncio.subprocess.PIPE


@dataclass
class DataclassMocker:
    id: int
    status: str


dataclass_obj = DataclassMocker(id=20, status="active")


def test_get_field_value():
    item = {"data": "some data", "more data": 100}
    assert get_field_value(item, "data") == "some data"
    assert get_field_value(item, "more data") == 100

    assert get_field_value(item=dataclass_obj, field="status") == "active"

    invalid = "some string"
    assert get_field_value(item=invalid, field="totally invalid") == None


def test_serialize():
    assert type(serialize(item=dataclass_obj)) == dict
    assert type(serialize(item={"some": "data"})) == dict


def test_paginate():
    test_snapshot = ["1", "2", "3", "4"]
    limit = 1
    page = 2

    assert paginate(page=page, limit=limit,
                    snapshot=test_snapshot) == (["2"], 4)


def test_group_by_keys():
    items = [
        {
            "name": "sparky",
            "day": "wednesday",
            "data": "some data"
        },
        {
            "name": "sparky",
            "day": "tuesday",
            "data": "some other data"
        }
    ]
    outer_key = "name"
    inner_key = "day"
    assert group_by_keys(items=items, outer_key=outer_key, inner_key=inner_key) == [
        {
            "sparky": {
                "tuesday": [items[1]],
                "wednesday": [items[0]]
            }
        }
    ]

# Mock async generator for stdout


class FakeStdout:
    def __init__(self, lines):
        self.lines = lines

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.lines:
            raise StopAsyncIteration
        return self.lines.pop(0)


@pytest.mark.asyncio
async def test_ps_stream_parses_and_updates_running_ps():
    # Simulate 2 good lines and one END signal
    line1 = b"2024-01-01T00:00:00Z,100,1,root,0.2,S,00:00,00:01,bash"
    line2 = b"2024-01-01T00:00:01Z,101,1,user,0.1,S,00:01,00:01,python"
    end_line = b"END"

    mock_process = AsyncMock()
    mock_process.stdout = FakeStdout(lines=[line1, line2, end_line])

    with patch("utils.run_script", return_value=mock_process):
        # clear shared state before testing
        with ps_lock:
            running_ps.clear()

        await ps_stream("fake_script.sh")

    # After "END", ps_deque_swap should have been flushed to running_ps
    with ps_lock:
        assert len(running_ps) == 2
        assert running_ps[0]["command"] == "bash"
        assert running_ps[1]["user"] == "user"


@pytest.mark.asyncio
async def test_io_stream():
    line1 = b"2025-01-01,00:00:00Z,1.00,2.00,3.00,4.00,5.00,6.00"
    line2 = b"2025-01-02,01:00:00Z,1.00,2.00,3.00,4.00,5.00,6.00"
    line3 = b"2025-01-03,02:00:00Z,1.00,2.00,3.00,4.00,5.00,6.00"

    mock_io = AsyncMock()
    mock_io.stdout = FakeStdout([line1, line2, line3])

    # iostats.clear()

    with patch("utils.run_script", return_value=mock_io):
        await io_stream("some_script.sh")

    assert len(iostats) == 3
    assert asdict(list(iostats)[0])["idle"] == 6.00


@pytest.mark.asyncio
async def test_alert_stream():
    # Set up a mock request that stays connected, then disconnects after 2 cycles
    mock_request = AsyncMock()
    mock_request.is_disconnected = AsyncMock(side_effect=[False, False, True])

    mock_alert = {
        "ip": "167.172.31.209",
        "msg": "High-risk SSH attack detected from DigitalOcean",
        "alert_type": AlertType.autobanned,
        "status": AlertStatus.unread,
        "timestamp": datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    }

    results = []

    async def consume_alerts():
        gen = alert_stream_delivery(mock_request)
        async for msg in gen:
            results.append(msg)
            if len(results) == 2:
                break

    task = asyncio.create_task(consume_alerts())
    await asyncio.sleep(0.1)  # Allow generator to yield keepalive
    await alerts_queue.put([mock_alert])  # Feed alert into the queue

    await asyncio.wait_for(task, timeout=2.0)

    # Assertions
    assert len(results) == 2
    assert results[0].strip() == "data: keepalive"

    assert results[1].startswith("data: ")
    payload = json.loads(results[1][6:].strip())
    assert isinstance(payload, list)
    assert payload[0]["ip"] == "167.172.31.209"


@pytest.mark.asyncio
async def test_host_info_async():
    with patch("utils.psutil.cpu_percent", return_value=12.3), \
            patch("utils.psutil.virtual_memory") as mock_vm, \
            patch("utils.psutil.disk_usage", return_value=Mock(percent=45.6)), \
            patch("utils.psutil.cpu_count", side_effect=[4, 8]), \
            patch("utils.psutil.boot_time", return_value=1000), \
            patch("utils.time.time", return_value=5000), \
            patch("utils.os.getloadavg", return_value=(0.5, 0.7, 0.9)):

        # Setup mock for virtual_memory().percent and .total
        mock_vm.return_value.percent = 67.8
        mock_vm.return_value.total = 8 * 1024**3  # 8 GB

        result = await host_info_async()

        assert result == {
            "cpu_percent": 12.3,
            "memory_percent": 67.8,
            "disk_percent": 45.6,
            "uptime_seconds": 4000,
            "load_avg": (0.5, 0.7, 0.9),
            "physical_cores": 4,
            "logical_cores": 8,
            "memory_gb": 8.0
        }
