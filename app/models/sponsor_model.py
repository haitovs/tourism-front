import enum

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer, String, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class SponsorTier(str, enum.Enum):
    premier = "premier"
    general = "general"
    diamond = "diamond"
    platinum = "platinum"
    gold = "gold"
    silver = "silver"
    bronze = "bronze"


class Sponsor(Base):
    __tablename__ = "sponsors"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    tier = Column(Enum(SponsorTier, name="sponsortier", create_type=False), nullable=False, server_default="general")
    logo = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    episode_links = relationship("EpisodeSponsor", back_populates="sponsor", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="episodes,sponsor")

    episodes = relationship("Episode",
                            secondary="episode_sponsors",
                            primaryjoin="Sponsor.id==EpisodeSponsor.sponsor_id",
                            secondaryjoin="Episode.id==EpisodeSponsor.episode_id",
                            viewonly=True,
                            lazy="selectin",
                            overlaps="episode_links,sponsor_links,episode,sponsor")

    site = relationship("Site", lazy="selectin")
