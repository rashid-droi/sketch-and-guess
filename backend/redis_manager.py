"""
In-memory pub/sub + room store — replaces Redis so the app runs without any external services.
API is kept identical to the original RedisManager so no other files need heavy changes.
"""
import json
import asyncio
from typing import Optional, Dict, List

class _PubSub:
    """Mimics redis-py's PubSub.listen() interface."""
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue

    async def listen(self):
        while True:
            msg = await self._queue.get()
            yield msg


class RedisManager:
    def __init__(self):
        self._rooms: Dict[str, str] = {}                      # room_id -> json string
        self._subscribers: Dict[str, List[asyncio.Queue]] = {} # channel -> queues

    # ── Room persistence ──────────────────────────────────────────────────────
    async def save_room(self, room_id: str, room_data: dict):
        self._rooms[f"room:{room_id}"] = json.dumps(room_data)

    async def get_room(self, room_id: str) -> Optional[dict]:
        data = self._rooms.get(f"room:{room_id}")
        return json.loads(data) if data else None

    # ── Pub / Sub ─────────────────────────────────────────────────────────────
    async def publish(self, room_id: str, message: dict):
        channel = f"channel:{room_id}"
        queues = self._subscribers.get(channel, [])
        payload = {"type": "message", "data": json.dumps(message)}
        for q in queues:
            await q.put(payload)

    async def subscribe(self, room_id: str) -> _PubSub:
        channel = f"channel:{room_id}"
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(channel, []).append(queue)
        return _PubSub(queue)


redis_manager = RedisManager()
