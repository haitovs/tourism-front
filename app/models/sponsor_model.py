import enum
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
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

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    tier = Column(Enum(SponsorTier, name="sponsortier", create_type=False), nullable=False, server_default="general")
    logo = Column(String, nullable=True)
