import json
import asyncio
import time
from typing import Optional, Dict, Any, TypeVar, Type
from pydantic import BaseModel
import logging
from contextlib import asynccontextmanager

T = TypeVar("T", bound=BaseModel)

class RedisClient:
    """
    Production-ready Redis client with a built-in in-memory fallback 
    to ensure the game works even if Redis is not installed.
    """
    def __init__(self, host="localhost", port=6379, db=0):
        self.is_connected = False
        self.memory_store: Dict[str, str] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        
        try:
            import redis.asyncio as redis
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            # We will attempt connection on first use
        except ImportError:
            self.redis = None
            logging.warning("redis-py not installed. Using in-memory fallback.")

    async def _check_connection(self):
        if self.redis and not self.is_connected:
            try:
                await asyncio.wait_for(self.redis.ping(), timeout=1.0)
                self.is_connected = True
                logging.info("Connected to real Redis server.")
            except Exception:
                self.is_connected = False
                self.redis = None
                logging.warning("Redis server not found. Falling back to in-memory mode.")

    async def set_json(self, key: str, data: BaseModel, ex: Optional[int] = None):
        await self._check_connection()
        json_data = data.model_dump_json() if hasattr(data, 'model_dump_json') else data.json()
        if self.is_connected:
            await self.redis.set(key, json_data, ex=ex)
        else:
            self.memory_store[key] = json_data

    async def get_json(self, key: str, model_type: Type[T]) -> Optional[T]:
        await self._check_connection()
        if self.is_connected:
            data = await self.redis.get(key)
        else:
            data = self.memory_store.get(key)
            
        if not data:
            return None
        return model_type.parse_raw(data)

    @asynccontextmanager
    async def lock(self, name: str, timeout: int = 10):
        await self._check_connection()
        lock_key = f"lock:{name}"
        identifier = str(time.time())
        acquired = False
        
        try:
            while not acquired:
                if self.is_connected:
                    acquired = await self.redis.set(lock_key, identifier, ex=timeout, nx=True)
                else:
                    # Simple in-memory lock
                    if lock_key not in self.memory_store:
                        self.memory_store[lock_key] = identifier
                        acquired = True
                
                if not acquired:
                    await asyncio.sleep(0.05)
            yield acquired
        finally:
            if self.is_connected:
                current_val = await self.redis.get(lock_key)
                if current_val == identifier:
                    await self.redis.delete(lock_key)
            else:
                if self.memory_store.get(lock_key) == identifier:
                    self.memory_store.pop(lock_key, None)

    async def publish_event(self, room_id: str, event_data: dict):
        await self._check_connection()
        channel = f"room:{room_id}"
        msg = json.dumps(event_data)
        
        if self.is_connected:
            await self.redis.publish(channel, msg)
        else:
            if channel in self.subscribers:
                for q in self.subscribers[channel]:
                    await q.put(msg)

    async def subscribe(self, room_id: str):
        await self._check_connection()
        channel = f"room:{room_id}"
        
        if self.is_connected:
            ps = self.redis.pubsub()
            await ps.subscribe(channel)
            return ps
        else:
            # Emulator Subscriber
            queue = asyncio.Queue()
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(queue)
            
            class MockPubSub:
                async def listen(self):
                    while True:
                        msg = await queue.get()
                        yield {"type": "message", "data": msg}
            return MockPubSub()

redis_client = RedisClient()
