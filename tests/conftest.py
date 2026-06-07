"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.youtube_healing.db import Base, User, Project, ProcessingLog


@pytest.fixture(scope="session")
def test_database():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_database):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=test_database)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        subscription_tier="pro",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        user_id=test_user.id,
        title="Test Project",
        status="draft",
        source_video_path="/tmp/test.mp4",
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def test_log(db_session, test_user, test_project):
    """Create a test processing log."""
    log = ProcessingLog(
        user_id=test_user.id,
        project_id=test_project.id,
        event_type="upload",
        message="Test event",
    )
    db_session.add(log)
    db_session.commit()
    return log
