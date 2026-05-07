from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import time

class GameStatus(str, Enum):
    LOBBY = "LOBBY"
    CHOOSING = "CHOOSING"
    DRAWING = "DRAWING"
    ROUND_END = "ROUND_END"
    NEXT_TURN = "NEXT_TURN"
    GAME_OVER = "GAME_OVER"
    PAUSED = "PAUSED"

class PlayerStatus(str, Enum):
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    DISCONNECTED = "DISCONNECTED"

class Player(BaseModel):
    player_id: str
    player_name: str
    score: int = 0
    round_score: int = 0
    streak: int = 0
    best_streak: int = 0
    total_correct_guesses: int = 0
    total_draw_points: int = 0
    guessed_this_round: bool = False
    status: PlayerStatus = PlayerStatus.CONNECTED
    last_seen: float = Field(default_factory=time.time)

class Room(BaseModel):
    room_id: str
    host_id: Optional[str] = None # Permanent creator ID
    version: int = 0
    status: GameStatus = GameStatus.LOBBY
    prev_status: Optional[GameStatus] = None # For resuming
    players: List[Player] = []
    
    # Rotation State
    current_drawer: Optional[str] = None
    drawer_queue: List[str] = []
    last_drawer_id: Optional[str] = None
    
    # Game State
    current_word: Optional[str] = None
    word_length: int = 0
    word_choices: List[str] = []
    timer: int = 60
    max_timer: int = 60
    current_pool: int = 100
    cycle_count: int = 1
    max_cycles: int = 1
    
    # Round Info
    current_round: int = 0
    total_rounds: int = 10 # Default, overridden by cycle logic
    round_won: bool = False
    hints_used: int = 0
    
    # Metadata
    created_at: float = Field(default_factory=time.time)
    last_update: float = Field(default_factory=time.time)

class CreateRoomRequest(BaseModel):
    player_id: str
    player_name: str

class JoinRoomRequest(BaseModel):
    room_id: str
    player_id: str
    player_name: str

class GameEvent(BaseModel):
    type: str
    room_id: str
    version: int
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any] = {}
