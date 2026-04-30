from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid

from .models import CreateRoomRequest, JoinRoomRequest, Room, Player
from .store import rooms
from .manager import manager
from .game_manager import start_game, handle_guess, start_next_turn
from .database import engine, Base, SessionLocal
from .redis_manager import redis_manager
from .db_models import User

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sketch & Guess Backend")

# Allow CORS for local testing with the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Optional: Log that persistence is enabled
    print("Redis Persistence enabled. Rooms will survive restarts.")

@app.post("/create-room", response_model=Room)
async def create_room(req: CreateRoomRequest):
    # Generate a short room ID (e.g., "7A8B")
    room_id = str(uuid.uuid4())[:6].upper()
    
    new_player = Player(player_id=req.player_id, player_name=req.player_name)
    new_room = Room(room_id=room_id, players=[new_player])
    
    rooms[room_id] = new_room
    await redis_manager.save_room(room_id, new_room.dict())
    return new_room

@app.post("/join-room", response_model=Room)
async def join_room(req: JoinRoomRequest):
    room_id = req.room_id.strip().upper()
    room = rooms.get(room_id)
    
    # If not in memory, try loading from Redis (handles server restarts)
    if not room:
        room_data = await redis_manager.get_room(room_id)
        if room_data:
            room = Room(**room_data)
            rooms[room_id] = room

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    # Check if player is already in room
    for p in room.players:
        if p.player_id == req.player_id:
            # We can optionally just return the room here instead of throwing an error,
            # but raising an error ensures explicit joins.
            raise HTTPException(status_code=400, detail="Player already in room")
            
    # Add player to room
    new_player = Player(player_id=req.player_id, player_name=req.player_name)
    room.players.append(new_player)
    
    # Persist the update
    await redis_manager.save_room(room_id, room.dict())
    
    return room

@app.post("/start-game/{room_id}")
async def trigger_game_start(room_id: str):
    room_id = room_id.upper()
    success = await start_game(room_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot start game. Check player count or room ID.")
    return {"status": "started"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str = None):
    room_id = room_id.strip().upper()
    
    # Check if room exists in memory or Redis
    if room_id not in rooms:
        room_data = await redis_manager.get_room(room_id)
        if room_data:
            rooms[room_id] = Room(**room_data)
        else:
            await websocket.close(code=1008)
            return

    await manager.connect(websocket, room_id)
    
    # Broadcast join to others
    if player_id:
        from .game_manager import get_leaderboard
        room = rooms.get(room_id)
        if room:
            player = next((p for p in room.players if p.player_id == player_id), None)
            display_name = player.player_name if player else player_id
            
            await redis_manager.publish(room_id, {
                "type": "game_event",
                "data": {"event": "player_joined", "details": f"{display_name} joined"}
            })
            
            await redis_manager.publish(room_id, {
                "type": "score_update",
                "data": {"leaderboard": get_leaderboard(room)}
            })
    
    # Subscribe to Redis for cross-instance broadcasts
    pubsub = await redis_manager.subscribe(room_id)
    
    async def redis_listener():
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                await websocket.send_text(msg["data"])

    import asyncio
    rtask = asyncio.create_task(redis_listener())
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Inject player details so everyone knows who sent the message
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and player_id:
                room = rooms.get(room_id)
                if room:
                    player = next((p for p in room.players if p.player_id == player_id), None)
                    if player:
                        data["data"]["player_id"] = player.player_id
                        data["data"]["player_name"] = player.player_name

            # 1. Publish to Redis (broadcasts to all instances)
            await redis_manager.publish(room_id, data)
            # 2. Local side-effects (e.g. guess checking)
            if data.get("type") == "chat" and player_id:
                await handle_guess(room_id, player_id, data.get("data", {}).get("message", ""))
            
    except WebSocketDisconnect:
        rtask.cancel()
        manager.disconnect(websocket, room_id)
        
        # Safe cleanup
        room = rooms.get(room_id)
        if room:
            leaving_player = next((p for p in room.players if p.player_id == player_id), None)
            if leaving_player:
                room.players.remove(leaving_player)
                
                # Check if we need to rotate turn
                if player_id == room.current_drawer and room.players:
                    await start_next_turn(room_id)
                
                # Broadcast departure
                await redis_manager.publish(room_id, {
                    "type": "game_event",
                    "data": {"event": "player_left", "details": f"{leaving_player.player_name} left"}
                })
                
                # Update leaderboard
                from .game_manager import get_leaderboard
                await redis_manager.publish(room_id, {
                    "type": "score_update",
                    "data": {"leaderboard": get_leaderboard(room)}
                })
