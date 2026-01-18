from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class ExpoSector(Base):
    __tablename__ = "expo_sectors"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    header = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    extended_description = Column(Text, nullable=True)
    logo = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    images = relationship(
        "ExpoSectorImage",
        back_populates="sector",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ExpoSectorImage.id",
    )


class ExpoSectorImage(Base):
    __tablename__ = "expo_sector_images"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    sector_id = Column(Integer, ForeignKey("expo_sectors.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)

    sector = relationship("ExpoSector", back_populates="images", lazy="joined")
