from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class GameStatus(str, Enum):
    LOBBY = "LOBBY"
    IN_PROGRESS = "IN_PROGRESS"
    ROUND_END = "ROUND_END"

class Player(BaseModel):
    player_id: str
    player_name: str
    score: int = 0

class Room(BaseModel):
    room_id: str
    players: List[Player] = []
    status: GameStatus = GameStatus.LOBBY
    current_drawer: Optional[str] = None # player_id
    current_word: Optional[str] = None
    drawer_index: int = -1
    timer: int = 60
    round_won: bool = False
    round_won_processed: bool = False
    
class CreateRoomRequest(BaseModel):
    player_id: str
    player_name: str

class JoinRoomRequest(BaseModel):
    room_id: str
    player_id: str
    player_name: str
