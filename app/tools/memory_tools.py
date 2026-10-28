import asyncio

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy.exc import SQLAlchemyError

from app.logging_config import logger
from app.memory.store import get_all_user_preferences, load_user_preference, save_user_preference

@tool
async def remember_user_preference(key: str, value: str, config: RunnableConfig) -> str:
    """
    Save a durable fact about the student that should be remembered in every future
    conversation, not just this thread (e.g. key="favorite_language", value="Python",
    or key="learning_goal", value="pass the SQL exam"). Only call this when the
    student explicitly states something worth remembering long-term.
    """
    logger.info("Tool called: remember_user_preference | key='%s'", key)
    # user_id arrives through the LangGraph runtime config, not the model's arguments.
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        return "Could not save: no user_id was provided for this session."

    try:
        await asyncio.to_thread(save_user_preference, user_id, key, value)
    except SQLAlchemyError:
        return "Something went wrong while saving that to long-term memory."

    return f"Saved to long-term memory: {key} -> {value}"


@tool
async def recall_user_preference(query_key: str, config: RunnableConfig) -> str:
    """
    Look up a previously saved long-term preference about the student across ALL of
    their threads (e.g. query_key="language" to recall their favorite programming
    language). Use this before asking the student something you may already know.
    """
    logger.info("Tool called: recall_user_preference | query_key='%s'", query_key)
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        return "Could not recall: no user_id was provided for this session."

    value = await asyncio.to_thread(load_user_preference, user_id, query_key)
    if value is None:
        return f"No long-term preference found for '{query_key}'."
    return f"Long-term memory found: {query_key} -> {value}"

@tool
async def recall_all_preferences(reason: str, config: RunnableConfig) -> str:
    """
    Look up EVERY durable fact saved about this student across all of their threads.
    Use this for broad questions like "what do you know about me?" or "what have I
    told you about myself?", where there is no single specific fact to search for.

    Args:
        reason: One short phrase on why you're calling this, e.g. "answering a
            personal question about the student".
    """
    logger.info("Tool called: recall_all_preferences | reason='%s'", reason)
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        return "Could not recall: no user_id was provided for this session."

    preferences = await asyncio.to_thread(get_all_user_preferences, user_id)
    if not preferences:
        return "No long-term preferences have been saved for this student yet."
    return "\n".join(f"{key}: {value}" for key, value in preferences.items())
"""LangChain tools that let the agent save and retrieve durable student facts."""
