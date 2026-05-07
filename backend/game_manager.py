import asyncio
import random
from .store import rooms
from .manager import manager
from .words import get_random_word, mask_word
from .models import GameStatus, Player
from .database import SessionLocal
from .db_models import User
from .redis_manager import redis_manager

def persist_score(player_id: str, player_name: str, added_score: int, streak: int = 0, is_correct: bool = False):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.player_id == player_id).first()
        if not user:
            user = User(
                player_id=player_id, 
                username=player_name, 
                total_score=added_score,
                highest_streak=streak,
                total_correct_guesses=1 if is_correct else 0
            )
            db.add(user)
        else:
            user.total_score += added_score
            if streak > user.highest_streak:
                user.highest_streak = streak
            if is_correct:
                user.total_correct_guesses += 1
        db.commit()
    finally:
        db.close()

def get_leaderboard(room):
    # Sort by total score, then streak, then correct guesses
    sorted_players = sorted(
        room.players, 
        key=lambda p: (p.score, p.streak, p.correct_guesses_count), 
        reverse=True
    )
    return [
        {
            "player_id": p.player_id, 
            "player_name": p.player_name, 
            "score": p.score,
            "round_score": p.round_score,
            "streak": p.streak,
            "correct_guesses": p.correct_guesses_count
        }
        for p in sorted_players
    ]

async def start_game(room_id: str):
    room = rooms.get(room_id)
    if not room or len(room.players) < 2:
        return False
        
    room.status = GameStatus.IN_PROGRESS
    room.current_round = 0
    
    # Initial Cycle Shuffle
    player_ids = [p.player_id for p in room.players]
    random.shuffle(player_ids)
    room.drawer_queue = player_ids
    room.last_drawer_id = None
    
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

    # Reset per-round state
    for p in room.players:
        p.round_score = 0
        p.guessed_this_round = False

    # 1. Handle Cycle Completion & Reshuffling
    if not room.drawer_queue:
        player_ids = [p.player_id for p in room.players]
        if len(player_ids) > 1:
            # Shuffle until the first person isn't the same as the last drawer
            for _ in range(10): # Avoid infinite loop
                random.shuffle(player_ids)
                if player_ids[0] != room.last_drawer_id:
                    break
        else:
            random.shuffle(player_ids)
        room.drawer_queue = player_ids

    # 2. Pick Next Drawer
    next_drawer_id = room.drawer_queue.pop(0)
    room.last_drawer_id = next_drawer_id
    room.current_drawer = next_drawer_id
    
    drawer = next((p for p in room.players if p.player_id == next_drawer_id), None)
    if not drawer: # Should not happen unless they left mid-transition
        return await start_next_turn(room_id)

    # 3. Pick word and reset state
    room.current_word = get_random_word()
    room.timer = 60
    room.max_timer = 60
    room.round_won = False
    room.round_won_processed = False
    room.hints_used = 0
    room.current_round += 1
    
    # Notify clients
    await redis_manager.publish(room_id, {
        "type": "new_turn",
        "data": {
            "drawer_id": drawer.player_id,
            "drawer_name": drawer.player_name,
            "masked_word": mask_word(room.current_word),
            "full_word": room.current_word,
            "word_length": len(room.current_word),
            "next_drawer_hint": room.drawer_queue[0] if room.drawer_queue else "Reshuffling..."
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
        
        # Automatic Hints at 45s, 30s, 15s
        new_hints = 0
        if room.timer == 45: new_hints = 1
        elif room.timer == 30: new_hints = 2
        elif room.timer == 15: new_hints = 3
        
        if new_hints > room.hints_used:
            room.hints_used = new_hints
            from .words import get_hint
            hint_masked = get_hint(room.current_word, room.hints_used)
            await redis_manager.publish(room_id, {
                "type": "hint_reveal",
                "data": {
                    "masked_word": hint_masked,
                    "hints_used": room.hints_used
                }
            })

        # Broadcast timer every second
        await redis_manager.publish(room_id, {
            "type": "timer_update",
            "data": {"seconds": room.timer}
        })
            
    if room.timer <= 0:
        await end_round(room_id)

async def end_round(room_id: str):
    room = rooms.get(room_id)
    if not room or room.round_won_processed:
        return
    
    room.round_won_processed = True
    room.status = GameStatus.ROUND_END
    
    # Calculate Drawer score: 25 points per correct guesser
    guessers = [p for p in room.players if p.guessed_this_round]
    drawer = next((p for p in room.players if p.player_id == room.current_drawer), None)
    
    if drawer:
        drawer_points = len(guessers) * 25
        # Perfect Round Bonus: if all other players guessed correctly
        if len(guessers) > 0 and len(guessers) == len(room.players) - 1:
            drawer_points += 50
            
        drawer.score += drawer_points
        drawer.round_score = drawer_points
        persist_score(drawer.player_id, drawer.player_name, drawer_points, drawer.streak)

    # Reset streaks for those who didn't guess (and aren't the drawer)
    for p in room.players:
        if p.player_id != room.current_drawer and not p.guessed_this_round:
            p.streak = 0

    # Broadcast summary
    summary_message = f"Round Over! The word was {room.current_word}"
    if room.timer <= 0 and not room.round_won:
        summary_message = f"Time's up! The word was {room.current_word}"

    await redis_manager.publish(room_id, {
        "type": "round_summary",
        "data": {
            "word": room.current_word,
            "message": summary_message,
            "leaderboard": get_leaderboard(room),
            "perfect_round": len(guessers) == len(room.players) - 1 if guessers else False
        }
    })
    
    # Freeze for 5 seconds for UX
    await asyncio.sleep(5)
    
    if room.current_round >= room.total_rounds:
        room.status = GameStatus.LOBBY
        room.current_round = 0
        await redis_manager.publish(room_id, {
            "type": "game_event",
            "data": {"event": "game_over", "details": "The game has ended!"}
        })
    else:
        room.status = GameStatus.IN_PROGRESS
        await start_next_turn(room_id)

async def handle_guess(room_id: str, player_id: str, guess_text: str):
    room = rooms.get(room_id)
    if not room or room.status != GameStatus.IN_PROGRESS:
        return
        
    # Anti-cheat: No guesses in the first second
    if room.timer > room.max_timer - 1:
        return

    # Drawer cannot guess
    if player_id == room.current_drawer:
        return

    # Find player
    guesser = next((p for p in room.players if p.player_id == player_id), None)
    if not guesser or guesser.guessed_this_round:
        return

    # Check guess
    if guess_text.strip().upper() == room.current_word:
        guesser.guessed_this_round = True
        guesser.correct_guesses_count += 1
        guesser.streak += 1
        
        # Calculate score with hint penalty: (100 - hints*20) * (timer / max_timer)
        max_possible = max(40, 100 - (room.hints_used * 20))
        points = int(max_possible * (room.timer / room.max_timer))
        
        # Streak Bonus
        bonus = 0
        if guesser.streak >= 5:
            bonus = 50
        elif guesser.streak >= 3:
            bonus = 20
            
        final_score = points + bonus
        guesser.score += final_score
        guesser.round_score = final_score
        
        persist_score(player_id, guesser.player_name, final_score, guesser.streak, is_correct=True)
            
        await redis_manager.publish(room_id, {
            "type": "correct_guess",
            "data": {
                "player_id": player_id,
                "player_name": guesser.player_name,
                "points": final_score,
                "streak": guesser.streak,
                "bonus": bonus
            }
        })

        # Check if all players (except drawer) have guessed
        active_guessers = [p for p in room.players if p.player_id != room.current_drawer]
        if all(p.guessed_this_round for p in active_guessers):
            room.round_won = True
            room.timer = 0
            await redis_manager.save_room(room_id, room.dict())
            await end_round(room_id)
        else:
            # Just update leaderboard for everyone else
            await redis_manager.publish(room_id, {
                "type": "score_update",
                "data": {"leaderboard": get_leaderboard(room)}
            })
