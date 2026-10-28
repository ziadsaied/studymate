import datetime as dt
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import LTM_DATABASE_URL
from app.logging_config import logger

# SQLite is shared by worker threads, so its default same-thread restriction is disabled.
ltm_engine = create_engine(
    LTM_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(ltm_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Fix vs. the lecture version: turn FK enforcement on for every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Each store operation opens a short-lived transaction from this session factory.
LTMSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ltm_engine)
LTMBase = declarative_base()


class StudentUser(LTMBase):
    """One row per student -- the identity long-term memory is keyed on."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    # Relationships let one user own both their sidebar history and durable facts.
    threads = relationship("UserThread", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("LongTermMemory", back_populates="user", cascade="all, delete-orphan")


class UserThread(LTMBase):
    """One row per conversation thread a student has had with StudyMate -- lets a
    sidebar UI list a student's past threads (see get_user_sidebar_history)."""

    __tablename__ = "user_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    thread_id = Column(String, nullable=False, unique=True)
    chat_title = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    user = relationship("StudentUser", back_populates="threads")


class LongTermMemory(LTMBase):
    """Durable facts about a student (e.g. favorite_language -> Python) that persist
    across every thread, unlike the checkpointer's per-thread message history."""

    __tablename__ = "long_term_memories"

    __table_args__ = (UniqueConstraint("user_id", "memory_key", name="uq_user_memory_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    memory_key = Column(String, nullable=False)
    memory_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    user = relationship("StudentUser", back_populates="memories")


def init_long_term_memory_db() -> None:
    """Create the memory tables on first startup; existing tables are left intact."""
    LTMBase.metadata.create_all(bind=ltm_engine)
    logger.info("Long-term memory tables ready (users, user_threads, long_term_memories).")
"""SQLAlchemy schema for users, chat threads, and durable student facts."""
