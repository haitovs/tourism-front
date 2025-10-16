from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer, String, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class AgendaDay(Base):
    __tablename__ = "agenda_days"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    label = Column(String(64), nullable=True)
    published = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    site = relationship("Site", lazy="selectin")
