from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(50), unique=True, index=True)
    username = Column(String(50))
    total_score = Column(Integer, default=0)
    highest_streak = Column(Integer, default=0)
    total_correct_guesses = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)

class RoomArchive(Base):
    __tablename__ = "room_archive"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(10), unique=True, index=True)
    status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
