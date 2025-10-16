# app/models/site_model.py
import enum

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, func)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    default_locale = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    domains = relationship("SiteDomain", back_populates="site", cascade="all, delete-orphan")
    members = relationship("UserSiteRole", back_populates="site", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"{self.name} [{self.slug}]"


class SiteDomain(Base):
    __tablename__ = "site_domains"
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    site = relationship("Site", back_populates="domains")

    def __str__(self) -> str:
        return self.domain


class SiteRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"


class UserSiteRole(Base):
    __tablename__ = "user_site_roles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(24), nullable=False)

    site = relationship("Site", back_populates="members")
    user = relationship("User")

    def __str__(self) -> str:
        uname = getattr(self.user, "username", f"user:{self.user_id}")
        sslug = getattr(self.site, "slug", f"site:{self.site_id}")
        return f"{uname} @ {sslug} ({self.role})"
