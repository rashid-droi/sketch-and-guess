import asyncio
from .store import rooms
from .manager import manager
from .words import get_random_word, mask_word
from .models import GameStatus, Player
from .database import SessionLocal
from .db_models import User
from .redis_manager import redis_manager

def persist_score(player_id: str, player_name: str, added_score: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.player_id == player_id).first()
        if not user:
            user = User(player_id=player_id, username=player_name, total_score=added_score)
            db.add(user)
        else:
            user.total_score += added_score
        db.commit()
    finally:
        db.close()

def get_leaderboard(room):
    # Return players sorted by score descending
    sorted_players = sorted(room.players, key=lambda p: p.score, reverse=True)
    return [
        {"player_id": p.player_id, "player_name": p.player_name, "score": p.score}
        for p in sorted_players
    ]

async def start_game(room_id: str):
    room = rooms.get(room_id)
    if not room or len(room.players) < 2:
        return False
        
    room.status = GameStatus.IN_PROGRESS
    await redis_manager.publish(room_id, {
        "type": "game_event",
        "data": {"event": "game_start", "details": "The game is starting!"}
    })
    
    await redis_manager.save_room(room_id, room.dict())
    await start_next_turn(room_id)
    return True

async def start_next_turn(room_id: str):
    room = rooms.get(room_id)
    if not room or room.status != GameStatus.IN_PROGRESS:
        return

    # Rotate drawer
    room.drawer_index = (room.drawer_index + 1) % len(room.players)
    drawer = room.players[room.drawer_index]
    room.current_drawer = drawer.player_id
    
    # Pick word
    room.current_word = get_random_word()
    room.timer = 60
    room.round_won = False
    
    # Send word to drawer vs masked to others
    # Since manager.broadcast sends to everyone, we have to handle individual messages manually
    # or just broadcast the masked word and then send a private update to the drawer if we had player-specific websockets.
    # For now, let's simplify: broadcast 'new_turn' with masked word, and expect drawer to know they are drawing.
    # Actually, let's use a broadcast for now and include the full word if we had user-id based routing.
    # Since our manager only tracks room-wide connections, we'll just broadcast the info.
    # In a more advanced version, manager would store {player_id: websocket}.
    
    await redis_manager.publish(room_id, {
        "type": "new_turn",
        "data": {
            "drawer_id": drawer.player_id,
            "drawer_name": drawer.player_name,
            "masked_word": mask_word(room.current_word),
            "full_word": room.current_word,
            "word_length": len(room.current_word)
        }
    })
    
    await redis_manager.save_room(room_id, room.dict())
    
    # Start timer loop
    asyncio.create_task(run_timer(room_id))

async def run_timer(room_id: str):
    room = rooms.get(room_id)
    if not room:
        return
        
    while room.timer > 0 and room.status == GameStatus.IN_PROGRESS and not room.round_won:
        await asyncio.sleep(1)
        room.timer -= 1
        
        # Broadcast timer every second for a smooth real-time countdown
        await redis_manager.publish(room_id, {
            "type": "timer_update",
            "data": {"seconds": room.timer}
        })
            
    if room.timer <= 0:
        await end_round(room_id)

async def end_round(room_id: str):
    room = rooms.get(room_id)
    if not room or room.round_won_processed: # Prevent duplicate end-of-round processing
        return
    
    room.round_won_processed = True
    
    # Broadcast the end message
    message = f"Round Over! The word was {room.current_word}"
    if room.timer <= 0 and not room.round_won:
        message = f"Time's up! The word was {room.current_word}"

    await redis_manager.publish(room_id, {
        "type": "game_event",
        "data": {
            "event": "round_end", 
            "details": message
        }
    })
    
    # Update scoreboard
    await redis_manager.publish(room_id, {
        "type": "score_update",
        "data": {"leaderboard": get_leaderboard(room)}
    })
    
    await asyncio.sleep(3)
    # Important: Reset the processed flag for the next turn
    room.round_won_processed = False
    await start_next_turn(room_id)

async def handle_guess(room_id: str, player_id: str, guess_text: str):
    room = rooms.get(room_id)
    if not room or room.status != GameStatus.IN_PROGRESS or room.round_won:
        return
        
    # Drawer cannot guess
    if player_id == room.current_drawer:
        return

    # Check guess
    if guess_text.strip().upper() == room.current_word:
        room.round_won = True
        
        # Find player names and award points
        guesser = next((p for p in room.players if p.player_id == player_id), None)
        drawer = next((p for p in room.players if p.player_id == room.current_drawer), None)
        
        if guesser:
            guesser.score += 100
            persist_score(player_id, guesser.player_name, 100)
        if drawer:
            drawer.score += 50
            persist_score(room.current_drawer, drawer.player_name, 50)
            
        await redis_manager.publish(room_id, {
            "type": "correct_guess",
            "data": {
                "player_id": player_id,
                "player_name": guesser.player_name if guesser else "Someone",
                "word": room.current_word,
                "scores": {p.player_id: p.score for p in room.players}
            }
        })

        # Broadcast explicit score update
        await redis_manager.publish(room_id, {
            "type": "score_update",
            "data": {"leaderboard": get_leaderboard(room)}
        })
        
        # Stop timer and transition
        room.timer = 0
        await redis_manager.save_room(room_id, room.dict())
        await end_round(room_id)
