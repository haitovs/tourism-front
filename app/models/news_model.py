from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func)

from app.core.db import Base


class News(Base):
    __tablename__ = "news"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    header = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    photo = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)
    is_published = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
