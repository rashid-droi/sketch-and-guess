from typing import Optional, Callable, Awaitable
from ..models.schemas import Room, GameEvent
from ..core.redis_client import redis_client
import time

class RoomRepository:
    @staticmethod
    def _get_key(room_id: str) -> str:
        return f"room:{room_id}:state"

    async def get_room(self, room_id: str) -> Optional[Room]:
        room = await redis_client.get_json(self._get_key(room_id), Room)
        if room:
            print(f"[DEBUG] [Repo] Fetched room {room_id} (v{room.version}) with {len(room.players)} players")
        return room

    async def save_room(self, room: Room):
        room.version += 1
        room.last_update = time.time()
        await redis_client.set_json(key=self._get_key(room.room_id), data=room)
        print(f"[DEBUG] [Repo] Saved room {room.room_id} (v{room.version}). Total players: {len(room.players)}")
        return room

    async def atomic_update(
        self, 
        room_id: str, 
        update_func: Callable[[Room], Awaitable[Room]]
    ) -> Optional[Room]:
        print(f"[DEBUG] [Repo] Starting atomic update for {room_id}...")
        async with redis_client.lock(room_id):
            room = await self.get_room(room_id)
            if not room:
                print(f"[DEBUG] [Repo] Atomic update failed: Room {room_id} not found")
                return None
            
            updated_room = await update_func(room)
            await self.save_room(updated_room)
            print(f"[DEBUG] [Repo] Atomic update success for {room_id} (v{updated_room.version})")
            return updated_room

    async def broadcast_event(self, room: Room, type: str, data: dict = {}):
        event = GameEvent(
            type=type,
            room_id=room.room_id,
            version=room.version,
            data=data
        )
        print(f"[DEBUG] [Repo] Broadcasting event '{type}' to room {room.room_id} (v{room.version})")
        await redis_client.publish_event(room.room_id, event.dict())

    async def broadcast_leaderboard(self, room: Room):
        # We transform players into a simplified leaderboard format
        leaderboard = [
            {
                "player_id": p.player_id,
                "player_name": p.player_name,
                "score": p.score,
                "round_score": p.round_score,
                "streak": p.streak,
                "status": p.status
            }
            for p in room.players
        ]
        await self.broadcast_event(room, "score_update", {"leaderboard": leaderboard})

room_repo = RoomRepository()
