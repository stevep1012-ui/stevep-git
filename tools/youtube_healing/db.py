"""
Database configuration and ORM models for YouTube Bird Studio.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./youtube_bird.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)

    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)

    subscription_tier = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"


class Project(Base):
    """Video project model."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(50), default="draft")

    source_video_path = Column(String(500), nullable=True)
    source_music_path = Column(String(500), nullable=True)
    output_video_path = Column(String(500), nullable=True)

    metadata = Column(JSON, nullable=True)
    policy_findings = Column(JSON, nullable=True)

    youtube_video_id = Column(String(255), nullable=True, index=True)
    instagram_media_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="projects")
    logs = relationship("ProcessingLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title={self.title}, status={self.status})>"


class ProcessingLog(Base):
    """Processing event log model."""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), default="info")
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="logs")
    project = relationship("Project", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ProcessingLog(id={self.id}, event={self.event_type}, severity={self.severity})>"


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create all tables)."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def drop_db():
    """Drop all tables (dangerous - dev only)."""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  Database dropped")


def get_session():
    """Get a database session (for non-FastAPI contexts)."""
    return SessionLocal()
