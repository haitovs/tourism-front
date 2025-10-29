import enum

from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer, String)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class TimerMode(str, enum.Enum):
    UNTIL_START = "UNTIL_START"
    UNTIL_END = "UNTIL_END"


class Timer(Base):
    __tablename__ = "timers"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(255), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    mode = Column(Enum(TimerMode), default=TimerMode.UNTIL_START)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    site = relationship("Site", lazy="selectin")
