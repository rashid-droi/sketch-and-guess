# Sketch & Guess: Multiplayer Engine Architecture

This document outlines the production-grade, distributed architecture of the Sketch & Guess game engine.

## 1. Core Philosophy: Redis-Authoritative State
The backend is **stateless**. No game data is stored in the memory of the Python process.
*   **Single Source of Truth**: All room data is persisted in **Redis**.
*   **Atomic Updates**: Every state change (Joining, Scoring, Transitioning) uses an **Atomic Update Pattern** with distributed locking.
*   **Distributed Synchronization**: Multiple backend instances stay in sync via **Redis Pub/Sub**.

---

## 2. Finite State Machine (FSM) Lifecycle
The game progresses through a strict, deterministic lifecycle managed by the `GameStateEngine`.

| State | Duration | Transition Trigger | Action |
| :--- | :--- | :--- | :--- |
| **LOBBY** | Infinite | Host Clicks "Start" | Resets scores, shuffles queue. |
| **CHOOSING** | 10s | Drawer Picks / Timeout | Generates 3 words for the drawer. |
| **DRAWING** | 60s | All Guessed / Timeout | Masked word shown; Canvas active. |
| **ROUND_END** | 5s | Auto-timer | Word reveal; leaderboard flash. |
| **GAME_OVER** | Infinite | Host Clicks "Play Again" | MVP celebration; Hot Reset option. |

---

## 3. Communication Flow (WebSocket Events)

### Outbound (Server -> Client)
*   `rehydration`: Sent immediately on connect. Contains the full authoritative room state.
*   `choosing_word`: Sent to the drawer with 3 options; sent to others as a status update.
*   `new_turn`: Signals the start of drawing; provides the full word to the drawer and masked word to others.
*   `timer_update`: Broadcast every second for perfect cross-client synchronization.
*   `correct_guess`: Triggered on a match. Contains points earned and streak data.
*   `score_update`: Pushes the full sorted leaderboard for reactive UI updates.

---

## 4. Competitive Mechanics

### Smart Word Masking
The `mask_word` algorithm reveals the first letter of every word while preserving spaces and punctuation:
*   `APPLE` -> `A _ _ _ _`
*   `ICE CREAM` -> `I _ _   C _ _ _ _`

### Scoring & MVP System
Points are calculated via a speed-based decay formula:
*   **Fastest Guesser**: Highest speed multiplier.
*   **Best Drawer**: Awarded bonus points for every player who guesses their drawing.
*   **Streak Bonus**: Consecutive correct guesses multiply the base score.

---

## 5. Technical Reliability Patterns

### Distributed Timer Management
The `RoomTimerManager` ensures that even if a backend instance restarts, only one active countdown task exists per room ID. 
*   Uses `asyncio.create_task` for non-blocking ticks.
*   Verifies state on every tick to prevent "Stray Timers."

### The "Hot Restart" (Play Again)
The "Play Again" system avoids the overhead of room creation:
1.  **Queue Reshuffle**: Randomizes player order for the new session.
2.  **State Scrubbing**: Zeroes out scores and streaks but maintains WebSocket connections.
3.  **Instant Start**: Bypasses the lobby waiting period for a "back-to-back" experience.

---

## 6. Implementation Checklist
*   [x] **Backend**: Atomic Redis Updates (Locking).
*   [x] **Backend**: Pub/Sub Broadcast Layer.
*   [x] **Backend**: Centralized FSM Engine.
*   [x] **Frontend**: Reactive Pinia Store.
*   [x] **Frontend**: State-Driven Overlays (Choosing, Round End, Game Over).
*   [x] **UX**: Confetti & Celebration Animations.
