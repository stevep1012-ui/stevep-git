"""Authentication and authorization middleware."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Optional, Callable, Any

from tools.youtube_healing.db import SessionLocal, User, ProcessingLog
from tools.youtube_healing.subscription import SubscriptionTier

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication error."""
    pass


class QuotaExceededError(Exception):
    """Quota exceeded error."""
    pass


def get_current_user(user_id: Optional[str] = None) -> Optional[User]:
    """Get current user from ID."""
    if not user_id:
        return None

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_id)).first()
        return user
    except (ValueError, Exception) as e:
        logger.warning(f"Failed to get user {user_id}: {e}")
        return None
    finally:
        session.close()


def require_auth(func: Callable) -> Callable:
    """Require authentication decorator."""
    @wraps(func)
    def wrapper(*args, user_id: Optional[str] = None, **kwargs) -> Any:
        user = get_current_user(user_id)
        if not user:
            raise AuthError("Authentication required")
        if not user.is_active:
            raise AuthError("User account is inactive")
        return func(*args, user=user, **kwargs)
    return wrapper


def check_subscription(tier: str) -> Callable:
    """Check minimum subscription tier."""
    tier_order = {
        SubscriptionTier.FREE.value: 0,
        SubscriptionTier.PRO.value: 1,
        SubscriptionTier.ENTERPRISE.value: 2,
    }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, user: User, **kwargs) -> Any:
            user_tier_value = tier_order.get(user.subscription_tier, 0)
            required_tier_value = tier_order.get(tier, 1)

            if user_tier_value < required_tier_value:
                raise QuotaExceededError(
                    f"Feature requires {tier} subscription. You have {user.subscription_tier}"
                )
            return func(*args, user=user, **kwargs)
        return wrapper
    return decorator


def log_event(
    user: User,
    event_type: str,
    message: str,
    project_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> None:
    """Log a user event to database."""

    session = SessionLocal()
    try:
        log = ProcessingLog(
            user_id=user.id,
            project_id=project_id,
            event_type=event_type,
            message=message,
            details=details,
        )
        session.add(log)
        session.commit()
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
        session.rollback()
    finally:
        session.close()
