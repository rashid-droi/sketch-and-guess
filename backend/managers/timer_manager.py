import asyncio
from typing import Dict, Callable, Awaitable
import logging

class RoomTimerManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}

    def start_timer(self, room_id: str, delay: float, callback: Callable[..., Awaitable[None]]):
        # 1. Cancel existing timer for this room
        self.cancel_timer(room_id)

        # 2. Define the background task
        async def timer_task():
            try:
                await asyncio.sleep(delay)
                await callback(room_id)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logging.error(f"Timer error in room {room_id}: {e}")
            finally:
                # Cleanup reference when done
                if self.tasks.get(room_id) == current_task:
                    del self.tasks[room_id]

        # 3. Start and store the task
        current_task = asyncio.create_task(timer_task())
        self.tasks[room_id] = current_task

    def cancel_timer(self, room_id: str):
        if room_id in self.tasks:
            self.tasks[room_id].cancel()
            del self.tasks[room_id]

timer_manager = RoomTimerManager()
