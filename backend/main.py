import os
import uuid
import json
import asyncio
import time
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

from .models.schemas import Room, Player, CreateRoomRequest, JoinRoomRequest, PlayerStatus, GameStatus
from .repositories.room_repository import room_repo
from .engine.fsm import game_engine
from .core.redis_client import redis_client

app = FastAPI(title="Sketch & Guess API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create-room")
async def create_room(request: CreateRoomRequest):
    room_id = str(uuid.uuid4())[:6].upper()
    print(f"[DEBUG] [API] Creating room {room_id} for {request.player_name}")
    
    new_player = Player(
        player_id=request.player_id,
        player_name=request.player_name
    )
    
    new_room = Room(
        room_id=room_id,
        host_id=request.player_id,
        players=[new_player]
    )
    
    await room_repo.save_room(new_room)
    return new_room

@app.post("/join-room")
async def join_room(request: JoinRoomRequest):
    print(f"[DEBUG] [API] Player {request.player_name} joining room {request.room_id}")
    async def logic(room: Room):
        # Check if player already in room (reconnect)
        existing = next((p for p in room.players if p.player_id == request.player_id), None)
        if existing:
            print(f"[DEBUG] [API] Player {request.player_id} already exists, marking as connected")
            existing.status = PlayerStatus.CONNECTED
        else:
            new_player = Player(
                player_id=request.player_id,
                player_name=request.player_name
            )
            room.players.append(new_player)
            print(f"[DEBUG] [API] Added player {request.player_name} to room {request.room_id}. Total: {len(room.players)}")
        return room

    room = await room_repo.atomic_update(request.room_id, logic)
    if not room:
        print(f"[DEBUG] [API] Join failed: Room {request.room_id} not found")
        raise HTTPException(status_code=404, detail="Room not found")
    
    # CRITICAL: Broadcast updated list to everyone ALREADY in the room
    # This ensures the creator sees the joiner immediately.
    await room_repo.broadcast_leaderboard(room)
    return room

@app.post("/start-game/{room_id}")
async def trigger_start(room_id: str):
    room_id = room_id.upper()
    print(f"\n[DEBUG] [START_GAME_CLICKED] Received API request for room: {room_id}")
    await game_engine.transition_to_starting(room_id)
    print(f"[DEBUG] [START_GAME_HANDLER] Transition function completed for: {room_id}\n")
    return {"status": "success"}

@app.post("/select-word/{room_id}")
async def select_word(room_id: str, player_id: str, word: str):
    room_id = room_id.upper()
    print(f"[DEBUG] [SELECT_WORD_CLICKED] Player {player_id} picked {word} in {room_id}")
    await game_engine.select_word(room_id, player_id, word)
    return {"status": "success"}

@app.post("/quit-game/{room_id}")
async def quit_game(room_id: str):
    room_id = room_id.upper()
    print(f"\n[DEBUG] [API] QUIT_GAME_REQUEST received for Room: {room_id}")
    await game_engine.transition_to_game_over(room_id)
    return {"status": "success"}

@app.post("/pause-game/{room_id}")
async def pause_game(room_id: str):
    room_id = room_id.upper()
    await game_engine.transition_to_paused(room_id)
    return {"status": "success"}

@app.post("/resume-game/{room_id}")
async def resume_game(room_id: str):
    room_id = room_id.upper()
    await game_engine.resume_game(room_id)
    return {"status": "success"}

@app.post("/reset-game/{room_id}")
async def reset_game(room_id: str):
    room_id = room_id.upper()
    await game_engine.transition_to_starting(room_id)
    return {"status": "success"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room_id = room_id.upper()
    player_id = websocket.query_params.get("player_id")
    print(f"[DEBUG] [WS] Connection request for room {room_id} from player {player_id}")
    
    if not player_id:
        await websocket.close(code=4003)
        return

    await websocket.accept()
    print(f"[DEBUG] [WS] Connection accepted for {player_id} in {room_id}")
    
    # CRITICAL: Mark player as connected in Redis so they are included in the game queue
    async def mark_connected(room: Room):
        for p in room.players:
            if p.player_id == player_id:
                p.status = PlayerStatus.CONNECTED
        return room
    await room_repo.atomic_update(room_id, mark_connected)
    print(f"[DEBUG] [WS] Player {player_id} status set to CONNECTED in Redis")

    # 1. State Rehydration: Send full room state on connect
    room = await room_repo.get_room(room_id)
    if room:
        # Use model_dump_json to ensure perfect serialization
        room_data = json.loads(room.model_dump_json())
        
        # Inject dynamic fields like masked word for guessers
        from .engine.logic import mask_word
        if room.current_word:
            room_data["masked_word"] = mask_word(room.current_word, room.hints_used)
            room_data["word_length"] = len(room.current_word)
        else:
            room_data["masked_word"] = ""
            room_data["word_length"] = 0
            
        print(f"[DEBUG] [WS] Sending rehydration to {player_id} (v{room.version})")
        await websocket.send_json({
            "type": "rehydration",
            "data": room_data
        })
        
        # 2. Broadcast presence with friendly name
        player_name = next((p.player_name for p in room.players if p.player_id == player_id), player_id)
        await redis_client.publish_event(room_id, {
            "type": "game_event",
            "data": {"event": "player_joined", "details": f"{player_name} joined the room"}
        })
        
        # 3. Force room-wide player list update
        await room_repo.broadcast_leaderboard(room)

    # 4. Subscribe to Redis events for this room
    pubsub = await redis_client.subscribe(room_id)
    
    async def redis_listener():
        try:
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    await websocket.send_text(msg["data"])
        except Exception as e:
            print(f"[DEBUG] [WS] Redis listener error: {e}")

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            # Handle incoming client messages (Chat, Draw, Choice)
            data = await websocket.receive_json()
            msg_type = data.get("type")
            msg_payload = data.get("data", {})
            
            # Enrich with player info
            msg_payload["player_id"] = player_id
            
            if msg_type == "chat":
                # Check for guess
                guess_text = msg_payload.get("message", "")
                await game_engine.handle_guess(room_id, player_id, guess_text)
                
            # Publish event to everyone in the room
            await redis_client.publish_event(room_id, data)
            
    except WebSocketDisconnect:
        print(f"[DEBUG] [WS] Player {player_id} disconnected from {room_id}")
        listener_task.cancel()
        
        async def disconnect_logic(room: Room):
            player = next((p for p in room.players if p.player_id == player_id), None)
            if player:
                player.status = PlayerStatus.RECONNECTING
            return room
            
        await room_repo.atomic_update(room_id, disconnect_logic)
        
    except Exception as e:
        print(f"[DEBUG] [WS] Error: {e}")
        listener_task.cancel()
