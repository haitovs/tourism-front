from sqlalchemy import Column, DateTime, ForeignKey, Integer, func

from app.core.db import Base


class Statistics(Base):
    __tablename__ = "statistics"

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    episodes = Column(Integer, nullable=False, default=0)
    delegates = Column(Integer, nullable=False, default=0)
    speakers = Column(Integer, nullable=False, default=0)
    companies = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
