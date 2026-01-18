from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Episode(Base):
    __tablename__ = "episodes"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("agenda_days.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    description_md = Column(Text, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255), nullable=True)

    published = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=True)

    hero_image_url = Column(String(512), nullable=True)
    slug = Column(String(255), nullable=True, unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("day_id", "title", name="uq_episode_day_title"),)

    # ----- Speakers
    speaker_links = relationship("EpisodeSpeaker", back_populates="episode", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="speakers,episode")
    speakers = relationship("Speaker",
                            secondary="episode_speakers",
                            primaryjoin="Episode.id==EpisodeSpeaker.episode_id",
                            secondaryjoin="Speaker.id==EpisodeSpeaker.speaker_id",
                            viewonly=True,
                            lazy="selectin",
                            overlaps="speaker_links,episode_links,episode,speaker")

    # ----- Moderators
    moderator_links = relationship("EpisodeModerator", back_populates="episode", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="moderators,episode")
    moderators = relationship("Moderator",
                              secondary="episode_moderators",
                              primaryjoin="Episode.id==EpisodeModerator.episode_id",
                              secondaryjoin="Moderator.id==EpisodeModerator.moderator_id",
                              viewonly=True,
                              lazy="selectin",
                              overlaps="moderator_links,episode_links,episode,moderator")

    # ----- Sponsors
    sponsor_links = relationship("EpisodeSponsor", back_populates="episode", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin", overlaps="sponsors,episode")
    sponsors = relationship("Sponsor",
                            secondary="episode_sponsors",
                            primaryjoin="Episode.id==EpisodeSponsor.episode_id",
                            secondaryjoin="Sponsor.id==EpisodeSponsor.sponsor_id",
                            viewonly=True,
                            lazy="selectin",
                            overlaps="sponsor_links,episode_links,episode,sponsor")

    site = relationship("Site", lazy="selectin")


class EpisodeSpeaker(Base):
    __tablename__ = "episode_speakers"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    speaker_id = Column(Integer, ForeignKey("speakers.id", ondelete="CASCADE"), primary_key=True)
    role_label = Column(String(64), nullable=True)
    sort_order = Column(Integer, nullable=True)

    # ⬇️ FIXED: back_populates must target the *link* relationships
    episode = relationship("Episode", back_populates="speaker_links", lazy="joined", overlaps="speakers,speaker_links")
    speaker = relationship("Speaker", back_populates="episode_links", lazy="joined", overlaps="episodes,episode_links")


class EpisodeModerator(Base):
    __tablename__ = "episode_moderators"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    moderator_id = Column(Integer, ForeignKey("moderators.id", ondelete="CASCADE"), primary_key=True)
    sort_order = Column(Integer, nullable=True)

    episode = relationship("Episode", back_populates="moderator_links", lazy="joined", overlaps="moderators,moderator_links")
    moderator = relationship("Moderator", back_populates="episode_links", lazy="joined", overlaps="episodes,episode_links")


class EpisodeSponsor(Base):
    __tablename__ = "episode_sponsors"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id", ondelete="CASCADE"), primary_key=True)
    tier_override = Column(String(32), nullable=True)
    sort_order = Column(Integer, nullable=True)

    episode = relationship("Episode", back_populates="sponsor_links", lazy="joined", overlaps="sponsors,sponsor_links")
    sponsor = relationship("Sponsor", back_populates="episode_links", lazy="joined", overlaps="episodes,episode_links")
