from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Integer, String, Text, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Speaker(Base):
    __tablename__ = "speakers"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    photo = Column(String(255), nullable=True)
    company_photo = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    social_links = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    episode_links = relationship("EpisodeSpeaker", back_populates="speaker", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="episodes,speaker")

    episodes = relationship("Episode",
                            secondary="episode_speakers",
                            primaryjoin="Speaker.id==EpisodeSpeaker.speaker_id",
                            secondaryjoin="Episode.id==EpisodeSpeaker.episode_id",
                            viewonly=True,
                            lazy="selectin",
                            overlaps="episode_links,speaker_links,episode,speaker")

    site = relationship("Site", lazy="selectin")
