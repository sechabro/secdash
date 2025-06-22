import asyncio
import json
import logging
import threading
from asyncio import Queue
from collections import deque
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Awaitable, Callable, Optional, Union

from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(
            self,
            data_fn: Callable[[Optional[any]], Awaitable[any]] = None,
            deque: Optional[deque] = None,
            queue: Optional[asyncio.Queue] = None,
            script: str | None = None,
            group_fn: Callable[[Optional[any]], Awaitable[any]] | None = None

    ):
        self.script = script
        self.output = data_fn
        self.queue = queue
        self.deque = deque
        self.lock = threading.Lock()
        self.group_fn = group_fn

    async def run_script(self):
        return await asyncio.create_subprocess_exec(
            self.script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    async def queue_delivery(self, request: Request):
        old_snapshot = []
        yield "data: keepalive\n\n"
        try:
            while not await request.is_disconnected():
                serialized_alerts = await self.serialize(self.queue)
                if not serialized_alerts or serialized_alerts == old_snapshot:
                    yield "data: keepalive\n\n"
                    await asyncio.sleep(6)
                    continue
                logger.info(
                    f' Delivering {len(serialized_alerts)} queued alerts.')
                for alert in serialized_alerts:
                    if isinstance(alert.get("timestamp"), datetime):
                        alert["timestamp"] = alert["timestamp"].isoformat()
                yield f"data: {json.dumps(serialized_alerts)}\n\n"
                old_snapshot = serialized_alerts

            logger.info("⚠️ Client disconnected, clearing alert queue.")
            self.queue = asyncio.Queue()
        except Exception as e:
            logger.error(f"🚨 queue_delivery error: {e}")
            yield "event: error\ndata: {}\n\n"
        except asyncio.CancelledError:
            logger.info("Delivery loop cancelled.")

    async def deque_delivery(self, request: Request):
        old_snapshot = []
        try:
            while not await request.is_disconnected():
                serialized = await self.serialize(self.deque)
                new_snapshot = self.group_fn(
                    serialized) if self.group_fn else serialized

                if new_snapshot != old_snapshot:
                    yield f"data: {json.dumps(new_snapshot)}\n\n"
                    old_snapshot = new_snapshot

                await asyncio.sleep(1)
                yield "data: keepalive\n\n"
        except Exception as e:
            logger.error(f"🚨 deque_delivery error: {e}")
            yield "event: error\ndata: {}\n\n"

    async def serialize(self, items: Union[deque, Queue]):
        """Universal serializer for various deques and Queues"""
        if isinstance(items, deque):
            list_items = list(items)
        elif isinstance(items, Queue):
            list_items = []
            while not items.empty():
                item = await items.get()
                list_items.append(item)
        else:
            raise TypeError(f"Unsupported stream type: {type(items)}")
        return [
            asdict(item) if is_dataclass(item)
            else item
            for item in list_items
        ]
