#!/usr/bin/env python3
"""Database initialization script."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.youtube_healing.db import init_db, SessionLocal, User
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Initialize database."""

    db_url = os.getenv("DATABASE_URL", "sqlite:///./youtube_bird.db")
    logger.info(f"Initializing database: {db_url}")

    try:
        init_db()
        logger.info("✅ Tables created successfully")

        # Create default admin (dev only)
        if "sqlite" in db_url:
            session = SessionLocal()
            try:
                admin = User(
                    email="admin@youtube-bird.local",
                    full_name="Admin User",
                    subscription_tier="enterprise",
                    is_active=True,
                )
                session.add(admin)
                session.commit()
                logger.info(f"✅ Created admin user")
            except:
                session.rollback()
                logger.warning("⚠️  Admin user might already exist")
            finally:
                session.close()

        logger.info("✅ Database initialization complete!")

    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
