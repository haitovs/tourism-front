from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func)

from app.core.db import Base


class TermsOfUse(Base):
    __tablename__ = "terms_of_use"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, server_default="Terms of Use")
    version = Column(String, nullable=True)
    content_md = Column(Text, nullable=False)
    published = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
