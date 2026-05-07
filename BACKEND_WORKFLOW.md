# Sketch & Guess: Backend Engineering Guide

This document provides a deep technical trace of the backend's implementation patterns, focusing on concurrency, state transitions, and real-time synchronization.

## 1. The Concurrency Model: Atomic Persistence
To support thousands of concurrent players, we use a **Lock-Update-Release** pattern in the `RoomRepository`.

### Distributed Locking
Every room mutation (joining, guessing, starting) is wrapped in a Redis-based distributed lock:
```python
# lock_name = f"lock:{room_id}"
with redis.lock(lock_name):
    room = get_room(room_id)
    # Perform logic...
    save_room(room)
```
This ensures that even with 100 players guessing at once, the `score` and `version` of the room remain consistent.

---

## 2. The FSM Engine (Finite State Machine)
The `GameStateEngine` is the brain of the backend. It handles all logical transitions.

### Key Lifecycle Transitions:
*   **`transition_to_starting`**: Instantly shuffles the `drawer_queue`, clears all scores/streaks, and resets the `current_round`.
*   **`transition_to_choosing`**: Generates 3 random words from the `WORD_BANK` and starts a 10s `auto_pick_word` timer.
*   **`handle_guess`**: Intercepts chat messages, performs fuzzy matching, calculates points using the speed-decay formula, and awards points to both the Guesser and the Drawer.
*   **`transition_to_game_over`**: Aggregates room-wide stats to identify the **Speed MVP**, **Art MVP**, and **Streak MVP**.

---

## 3. Real-Time Sync: Redis Pub/Sub
We decouple the **State (Redis Keys)** from the **Events (Redis Pub/Sub)**.

1.  **State Save**: The room is saved to Redis as a JSON string for permanent "Ground Truth."
2.  **Event Dispatch**: An event is published to `room:{room_id}`.
3.  **Broadcast**: Every WebSocket listener attached to that room ID receives the message and pushes it to the client.

This allows for **Horizontal Scaling**: you can run 10 backend servers, and players in the same room will stay in sync regardless of which server they are connected to.

---

## 4. Timer & Task Management
We use a centralized `RoomTimerManager` to handle all countdowns.
*   **Non-Blocking**: Timers run as background `asyncio` tasks.
*   **Re-entrant Safe**: Before starting a new timer, the manager cancels any existing tasks for that room to prevent "Timer Stacking."
*   **Server Ticking**: The server broadcasts a `timer_update` every second. Clients do NOT run their own authoritative clocks; they simply display the server's value.

---

## 5. Scoring & Fuzzy Logic
Located in `engine/logic.py`:
*   **Fuzzy Matching**: `target.upper().replace(" ", "") == guess.upper().replace(" ", "")`.
*   **Score Decay**: `int((100 - (hints * 20)) * (remaining_time / max_time))`. 
*   **Drawer Bonus**: The drawer earns a fixed bonus for every player who guesses correctly, incentivizing clear drawing.

---

## 6. Schema Reference
*   **Room**: The top-level container (ID, Status, Drawer Queue).
*   **Player**: Individual state (Score, Streak, Guessed Status, Connection Status).
*   **GameEvent**: The standard envelope for all WebSocket communication (`type`, `data`).
