import time
import random
import asyncio
from math import ceil
from typing import Optional, List, Dict, Any
from ..models.schemas import Room, GameStatus, PlayerStatus, Player
from ..repositories.room_repository import room_repo
from ..managers.timer_manager import timer_manager

WORD_BANK = ["BANANA", "AIRPLANE", "COMPUTER", "MOUNTAIN", "GUITAR", "ELEPHANT", "PIZZA", "SUNGLASSES", "BICYCLE", "DINOSAUR", "HAMBURGER", "SNOWMAN"]

class GameStateEngine:
    async def transition_to_starting(self, room_id: str):
        room_id = room_id.upper()
        async def logic(room: Room):
            # Reset room state for a fresh start
            room.status = GameStatus.CHOOSING
            room.current_round = 0
            room.cycle_count = 1
            
            # Adaptive Cycle Logic: N < 10 players = 2 cycles, else 1
            connected_players = [p.player_id for p in room.players if p.status == PlayerStatus.CONNECTED]
            room.max_cycles = 2 if len(connected_players) < 10 else 1
            
            # Initialize Drawer Queue (Shuffled)
            random.shuffle(connected_players)
            room.drawer_queue = connected_players
            room.last_drawer_id = None
            
            # Reset Player stats
            for p in room.players:
                p.score = 0
                p.round_score = 0
                p.streak = 0
                p.best_streak = 0
                p.total_correct_guesses = 0
                p.total_draw_points = 0
                p.guessed_this_round = False
            
            return room

        room = await room_repo.atomic_update(room_id, logic)
        if room:
            await room_repo.broadcast_event(room, "game_start", {"max_cycles": room.max_cycles})
            await self.transition_to_next_turn(room_id)

    async def transition_to_next_turn(self, room_id: str):
        async def logic(room: Room):
            # Check if current cycle is complete
            if not room.drawer_queue:
                if room.cycle_count < room.max_cycles:
                    # Start SECOND CYCLE
                    room.cycle_count += 1
                    connected_players = [p.player_id for p in room.players if p.status == PlayerStatus.CONNECTED]
                    random.shuffle(connected_players)
                    # Prevent last drawer from drawing immediately again
                    if len(connected_players) > 1 and connected_players[0] == room.last_drawer_id:
                        connected_players[0], connected_players[-1] = connected_players[-1], connected_players[0]
                    room.drawer_queue = connected_players
                    print(f"[FSM] Cycle {room.cycle_count} starting for {room_id}")
                else:
                    # ALL CYCLES COMPLETE
                    room.status = GameStatus.GAME_OVER
                    return room

            # Pick next drawer
            room.current_drawer = room.drawer_queue.pop(0)
            room.last_drawer_id = room.current_drawer
            room.status = GameStatus.CHOOSING
            room.current_pool = 100 # Reset score pool
            room.timer = 15 # 15s to choose (auto-picks)
            
            # Auto-pick word for now to keep flow tempo high
            room.current_word = random.choice(WORD_BANK)
            room.word_length = len(room.current_word)
            return room

        room = await room_repo.atomic_update(room_id, logic)
        if room:
            if room.status == GameStatus.GAME_OVER:
                await self.transition_to_game_over(room_id)
            else:
                await room_repo.broadcast_event(room, "clear_canvas", {})
                await self.transition_to_drawing(room_id)

    async def transition_to_drawing(self, room_id: str):
        async def logic(room: Room):
            room.status = GameStatus.DRAWING
            room.current_round += 1
            room.round_won = False
            for p in room.players:
                p.guessed_this_round = False
                p.round_score = 0
            return room

        room = await room_repo.atomic_update(room_id, logic)
        if room:
            drawer = next((p for p in room.players if p.player_id == room.current_drawer), None)
            await room_repo.broadcast_event(room, "new_turn", {
                "drawer_id": room.current_drawer,
                "drawer_name": drawer.player_name if drawer else "Unknown",
                "full_word": room.current_word,
                "masked_word": room.current_word[0] + "_" * (len(room.current_word)-1),
                "word_length": room.word_length,
                "seconds": 60
            })
            asyncio.create_task(self.run_drawing_timer(room_id, 60))

    async def run_drawing_timer(self, room_id: str, seconds: int):
        for i in range(seconds, -1, -1):
            await asyncio.sleep(1)
            room = await room_repo.get_room(room_id)
            if not room or room.status != GameStatus.DRAWING: break
            await room_repo.broadcast_event(room, "timer_update", {"seconds": i})
            if i == 0: await self.transition_to_round_end(room_id)

    async def transition_to_round_end(self, room_id: str):
        async def logic(room: Room):
            # Final scoring: Remaining pool goes to drawer if ANYONE guessed
            any_guessed = any(p.guessed_this_round for p in room.players if p.player_id != room.current_drawer)
            if any_guessed:
                drawer = next((p for p in room.players if p.player_id == room.current_drawer), None)
                if drawer:
                    drawer.score += room.current_pool
                    drawer.total_draw_points += room.current_pool
            
            room.status = GameStatus.ROUND_END
            # Reset streaks for those who didn't guess
            for p in room.players:
                if p.player_id != room.current_drawer and not p.guessed_this_round:
                    p.streak = 0
            return room

        room = await room_repo.atomic_update(room_id, logic)
        if room:
            await room_repo.broadcast_leaderboard(room)
            await room_repo.broadcast_event(room, "round_ended", {"word": room.current_word, "delay": 5})
            asyncio.create_task(self.run_round_end_timer(room_id, 5))

    async def run_round_end_timer(self, room_id: str, seconds: int):
        for i in range(seconds, -1, -1):
            await asyncio.sleep(1)
            room = await room_repo.get_room(room_id)
            if not room or room.status != GameStatus.ROUND_END: break
            await room_repo.broadcast_event(room, "timer_update", {"seconds": i})
            if i == 0: await self.transition_to_next_turn(room_id)

    async def handle_guess(self, room_id: str, player_id: str, guess: str):
        async def logic(room: Room):
            if room.status != GameStatus.DRAWING or room.current_drawer == player_id:
                return room
            player = next((p for p in room.players if p.player_id == player_id), None)
            if not player or player.guessed_this_round: return room
            
            target = room.current_word.upper().replace(" ", "")
            if guess.upper().replace(" ", "") == target:
                player.guessed_this_round = True
                player.total_correct_guesses += 1
                player.streak += 1
                player.best_streak = max(player.best_streak, player.streak)
                
                # HALVING SCORE LOGIC:
                points = ceil(room.current_pool / 2)
                room.current_pool -= points
                player.score += points
                player.round_score = points
                
                # Check if everyone guessed
                guessers = [p for p in room.players if p.player_id != room.current_drawer and p.status == PlayerStatus.CONNECTED]
                if all(p.guessed_this_round for p in guessers):
                    room.round_won = True
                
                # Dynamic Reshuffle Trigger: After 2nd correct guess
                correct_count = sum(1 for p in room.players if p.guessed_this_round)
                if correct_count == 2:
                    room.last_drawer_id = "SHUFFLE_TRIGGERED" # Internal flag or just log
            return room

        room = await room_repo.atomic_update(room_id, logic)
        if room:
            player = next((p for p in room.players if p.player_id == player_id), None)
            if player and player.guessed_this_round:
                await room_repo.broadcast_event(room, "correct_guess", {
                    "player_id": player_id,
                    "player_name": player.player_name,
                    "points": player.round_score,
                    "remaining_pool": room.current_pool
                })
                await room_repo.broadcast_leaderboard(room)
                if room.round_won:
                    await self.transition_to_round_end(room_id)

    async def transition_to_game_over(self, room_id: str):
        async def logic(room: Room):
            room.status = GameStatus.GAME_OVER
            return room
        room = await room_repo.atomic_update(room_id, logic)
        if room:
            mvps = {
                "guesser": max(room.players, key=lambda p: p.total_correct_guesses, default=None),
                "drawer": max(room.players, key=lambda p: p.total_draw_points, default=None),
                "streak": max(room.players, key=lambda p: p.best_streak, default=None)
            }
            await room_repo.broadcast_event(room, "game_over", {
                "leaderboard": [p.model_dump() for p in sorted(room.players, key=lambda p: p.score, reverse=True)],
                "mvps": {k: (v.player_name if v else "None") for k,v in mvps.items()}
            })

    async def transition_to_paused(self, room_id: str):
        async def logic(room: Room):
            if room.status == GameStatus.PAUSED: return room
            room.prev_status = room.status
            room.status = GameStatus.PAUSED
            return room
        room = await room_repo.atomic_update(room_id, logic)
        if room:
            await room_repo.broadcast_event(room, "game_paused", {"by_host": True})

    async def resume_game(self, room_id: str):
        async def logic(room: Room):
            if room.status != GameStatus.PAUSED: return room
            room.status = room.prev_status or GameStatus.DRAWING
            return room
        room = await room_repo.atomic_update(room_id, logic)
        if room:
            await room_repo.broadcast_event(room, "game_resumed", {"status": room.status})
            if room.status == GameStatus.DRAWING:
                asyncio.create_task(self.run_drawing_timer(room_id, room.timer))

game_engine = GameStateEngine()
