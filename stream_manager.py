import asyncio
import json
import logging
import threading
from collections import deque
from dataclasses import asdict, is_dataclass
from typing import Awaitable, Callable, Optional

from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(
            self,
            data_fn: Callable[[Optional[any]], Awaitable[any]],
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

    async def get_output(self):
        data = await self.run_script() if self.script else None
        return await self.output(data)

    async def queue_delivery(self, request: Request):
        yield "data: keepalive\n\n"
        while not await request.is_disconnected():
            try:
                if self.queue.qsize() == self.queue.maxsize:
                    data_batch = []
                    while not self.queue.empty():
                        data_batch.append(await self.queue.get())
                    yield f"data: {json.dumps(data_batch)}\n\n"
                else:
                    await asyncio.sleep(1)
                    yield "data: keepalive\n\n"
            except asyncio.TimeoutError:
                yield "data: keepalive\n\n"

    async def deque_delivery(self, request: Request):
        old_snapshot = []
        try:
            while not await request.is_disconnected():
                serialized = self.serialize(self.deque)
                new_snapshot = self.group_fn(
                    serialized) if self.group_fn else serialized

                if new_snapshot != old_snapshot:
                    yield f"data: {json.dumps(new_snapshot)}\n\n"
                    old_snapshot = new_snapshot

                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"🚨 deque_delivery error: {e}")
            yield "event: error\ndata: {}\n\n"

    def serialize(self, items: deque):
        """Universal serializer for dicts and dataclasses."""
        list_items = list(items)
        return [
            asdict(item) if is_dataclass(item)
            else item
            for item in list_items
        ]
