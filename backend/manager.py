from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # room_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str, exclude: WebSocket = None):
        if room_id not in self.active_connections:
            return
            
        connections = self.active_connections[room_id]
        if not connections:
            return

        # Prepare tasks for parallel execution
        tasks = []
        for connection in connections:
            if connection != exclude:
                tasks.append(connection.send_json(message))
        
        if tasks:
            # Use return_exceptions=True so one bad connection doesn't kill the whole broadcast
            await asyncio.gather(*tasks, return_exceptions=True)

manager = ConnectionManager()
