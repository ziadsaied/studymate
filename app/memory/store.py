from contextlib import contextmanager

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.logging_config import logger
from app.memory.models import LTMSessionLocal, LongTermMemory, StudentUser, UserThread


@contextmanager
def ltm_session():
    """Commit successful database work and roll back SQL failures automatically."""
    db = LTMSessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_or_create_user(user_id: str) -> str:
    """Ensure the stable user identity exists before saving threads or preferences."""
    try:
        with ltm_session() as db:
            user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            if not user:
                db.add(StudentUser(id=user_id, username=user_id))
                logger.info("Long-term memory: created new user '%s'.", user_id)
            return user_id
    except SQLAlchemyError:
        logger.exception("Failed to get/create user '%s'.", user_id)
        raise


def list_users() -> list:
    """Return the available local profiles, oldest first."""
    with ltm_session() as db:
        users = db.query(StudentUser).order_by(StudentUser.created_at.asc()).all()
        return [{"id": user.id, "username": user.username} for user in users]


def get_user_profile(user_id: str) -> dict | None:
    """Return one registered profile, if it exists."""
    with ltm_session() as db:
        user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
        return {"id": user.id, "username": user.username} if user else None


def get_or_create_user_by_name(username: str) -> dict:
    """Find or register a password-free local profile by its display name.

    ``local_student`` was the single-user identity used by earlier versions.
    Claiming the name Ziad upgrades that legacy profile in place, so its chats and
    durable memories remain available instead of being copied or lost.
    """
    cleaned_name = " ".join(username.split())
    if not cleaned_name:
        raise ValueError("A user name is required.")

    try:
        with ltm_session() as db:
            user = (
                db.query(StudentUser)
                .filter(func.lower(StudentUser.username) == cleaned_name.lower())
                .first()
            )
            if user:
                return {"id": user.id, "username": user.username}

            # Preserve data created before the multi-profile UI existed.
            if cleaned_name.casefold() == "ziad":
                legacy_user = db.query(StudentUser).filter(StudentUser.id == "local_student").first()
                if legacy_user:
                    legacy_user.username = cleaned_name
                    logger.info("Migrated legacy local profile to '%s'.", cleaned_name)
                    return {"id": legacy_user.id, "username": legacy_user.username}

            user = StudentUser(username=cleaned_name)
            db.add(user)
            db.flush()
            logger.info("Long-term memory: created new user '%s'.", cleaned_name)
            return {"id": user.id, "username": user.username}
    except SQLAlchemyError:
        logger.exception("Failed to get/create local profile '%s'.", cleaned_name)
        raise


def get_or_create_thread(user_id: str, thread_id: str, chat_title: str) -> None:
    """Register a thread once so it can appear in the sidebar history."""
    try:
        with ltm_session() as db:
            existing = db.query(UserThread).filter(UserThread.thread_id == thread_id).first()
            if existing:
                return
            db.add(UserThread(user_id=user_id, thread_id=thread_id, chat_title=chat_title))
            logger.info("Long-term memory: registered thread '%s' for user '%s'.", thread_id, user_id)
    except SQLAlchemyError:
        logger.exception("Failed to register thread '%s' for user '%s'.", thread_id, user_id)
        raise


def get_user_sidebar_history(user_id: str) -> list:
    """Return newest-first chat metadata for one user's sidebar."""
    with ltm_session() as db:
        threads = (
            db.query(UserThread)
            .filter(UserThread.user_id == user_id)
            .order_by(UserThread.created_at.desc())
            .all()
        )
        return [{"thread_id": t.thread_id, "title": t.chat_title, "created_at": t.created_at} for t in threads]


def user_owns_thread(user_id: str, thread_id: str) -> bool:
    """Check ownership before exposing a checkpoint's conversation history."""
    with ltm_session() as db:
        return (
            db.query(UserThread.id)
            .filter(UserThread.user_id == user_id, UserThread.thread_id == thread_id)
            .first()
            is not None
        )


def get_thread_owner(thread_id: str) -> str | None:
    """Return a thread's owner so a UUID from another profile cannot be reused."""
    with ltm_session() as db:
        thread = db.query(UserThread).filter(UserThread.thread_id == thread_id).first()
        return thread.user_id if thread else None


def save_user_preference(user_id: str, key: str, value: str) -> str:
    """Insert a durable fact or update its value when the key already exists."""
    try:
        with ltm_session() as db:
            memory = (
                db.query(LongTermMemory)
                .filter(LongTermMemory.user_id == user_id, LongTermMemory.memory_key == key)
                .first()
            )
            if memory:
                memory.memory_value = value
                action = "updated"
            else:
                db.add(LongTermMemory(user_id=user_id, memory_key=key, memory_value=value))
                action = "saved"
            logger.info("Long-term memory %s: '%s' -> '%s' (user '%s').", action, key, value, user_id)
            return action
    except SQLAlchemyError:
        logger.exception("Failed to save preference '%s' for user '%s'.", key, user_id)
        raise


def load_user_preference(user_id: str, query_key: str):
    """Find a stored fact whose key resembles the model's requested key."""
    with ltm_session() as db:
        memory = (
            db.query(LongTermMemory)
            .filter(LongTermMemory.user_id == user_id, LongTermMemory.memory_key.like(f"%{query_key}%"))
            .first()
        )
        return memory.memory_value if memory else None


def get_all_user_preferences(user_id: str) -> dict:
    """Load every durable fact for broad personal-memory questions."""
    with ltm_session() as db:
        memories = db.query(LongTermMemory).filter(LongTermMemory.user_id == user_id).all()
        return {m.memory_key: m.memory_value for m in memories}
"""Transactional helper functions for the long-term-memory SQLite database."""
