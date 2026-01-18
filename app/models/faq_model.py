from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func)

from app.core.db import Base


class FAQ(Base):
    __tablename__ = "faqs"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer_md = Column(Text, nullable=False)
    published = Column(Boolean, nullable=False, server_default="true")
    sort_order = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
