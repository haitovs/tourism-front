from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Moderator(Base):
    __tablename__ = "moderators"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    episode_links = relationship("EpisodeModerator", back_populates="moderator", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="episodes,moderator")
    episodes = relationship("Episode",
                            secondary="episode_moderators",
                            primaryjoin="Moderator.id==EpisodeModerator.moderator_id",
                            secondaryjoin="Episode.id==EpisodeModerator.episode_id",
                            viewonly=True,
                            lazy="selectin",
                            overlaps="episode_links,moderator_links,episode,moderator")

    site = relationship("Site", lazy="selectin")
