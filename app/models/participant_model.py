import enum

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer, String, Text, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class ParticipantRole(str, enum.Enum):
    expo = "expo"
    forum = "forum"
    both = "both"


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    # Basic participant fields
    name = Column(String(255), nullable=False)
    role = Column(Enum(ParticipantRole, name="participant_role", create_type=False), nullable=False, server_default="forum")
    bio = Column(Text, nullable=True)

    # Optional media / contact
    logo = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    images = relationship(
        "ParticipantImage",
        back_populates="participant",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ParticipantImage.id",
    )


class ParticipantImage(Base):
    __tablename__ = "participant_images"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)

    participant = relationship("Participant", back_populates="images", lazy="joined")
