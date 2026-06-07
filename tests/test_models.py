"""Tests for database models."""

import pytest
from tools.youtube_healing.db import User, Project, ProcessingLog


def test_user_creation(db_session):
    """Test creating a user."""
    user = User(
        email="user@example.com",
        full_name="John Doe",
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter(User.email == "user@example.com").first()
    assert retrieved is not None
    assert retrieved.email == "user@example.com"
    assert retrieved.subscription_tier == "free"
    assert retrieved.is_active is True


def test_user_unique_email(db_session, test_user):
    """Test that email must be unique."""
    duplicate = User(
        email=test_user.email,
        full_name="Duplicate",
    )
    db_session.add(duplicate)

    with pytest.raises(Exception):
        db_session.commit()


def test_project_creation(db_session, test_user):
    """Test creating a project."""
    project = Project(
        user_id=test_user.id,
        title="New Project",
        status="processing",
    )
    db_session.add(project)
    db_session.commit()

    retrieved = db_session.query(Project).filter(Project.title == "New Project").first()
    assert retrieved is not None
    assert retrieved.user_id == test_user.id


def test_project_relationship(db_session, test_user, test_project):
    """Test project-user relationship."""
    assert test_project.user_id == test_user.id
    assert test_project in test_user.projects


def test_processing_log_creation(db_session, test_log):
    """Test creating a processing log."""
    assert test_log.event_type == "upload"
    assert test_log.message is not None


def test_timestamps(db_session, test_user):
    """Test that timestamps are auto-created."""
    assert test_user.created_at is not None
    assert test_user.updated_at is not None
