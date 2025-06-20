import asyncio
import json
from collections import deque
from dataclasses import asdict, is_dataclass
from typing import Awaitable, Callable, Optional

from fastapi import Request


class StreamManager:
    def __init__(
            self,
            data_fn: Callable[[Optional[any]], Awaitable[any]],
            deque: Optional[deque] = None,
            queue: Optional[asyncio.Queue] = None,
            script: str | None = None,

    ):
        self.script = script
        self.output = data_fn
        self.queue = queue
        self.deque = deque

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
                    # print(f' data to deliver: {json.dumps([data])}')
                else:
                    await asyncio.sleep(1)
                    yield "data: keepalive\n\n"
            except asyncio.TimeoutError:
                yield "data: keepalive\n\n"

    async def deque_delivery(self, request: Request):
        old_snapshot = []
        while not await request.is_disconnected():
            new_snapshot = list(self.deque)
            if new_snapshot != old_snapshot:
                is_dc = is_dataclass(
                    new_snapshot[0]) if new_snapshot else False
                serialized = [
                    asdict(item) if is_dc else item for item in new_snapshot
                ]
                yield f"data: {json.dumps(serialized)}\n\n"
            await asyncio.sleep(1)
