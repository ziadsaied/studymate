import asyncio

from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from app.graph.builder import get_compiled_app
from app.logging_config import logger
from app.memory.store import get_or_create_thread, get_or_create_user
from app.schemas import UserRequest


async def run_agentic_rag(raw_request: dict) -> dict:
    """Validate a request, establish its identity, and return the graph's final answer."""
    try:
        request = UserRequest(**raw_request)
    except ValidationError as e:
        logger.warning("Validation Error: Invalid input parameters.")
        return {"error": "Invalid input format.", "details": e.errors()}

    user_id = request.user_id or request.session_id
    await asyncio.to_thread(get_or_create_user, user_id)
    await asyncio.to_thread(
        get_or_create_thread, user_id, thread_id=request.session_id, chat_title=request.query[:60]
    )

    # LangGraph uses thread_id for short-term checkpoints; tools use user_id for durable memory.
    config = {
        "configurable": {"thread_id": request.session_id, "user_id": user_id},
        "recursion_limit": 15,
    }
    logger.info(
        "run_agentic_rag: thread_id='%s' | user_id='%s' | query='%s'",
        request.session_id, user_id, request.query,
    )

    async with get_compiled_app() as graph_app:
        final_state = await graph_app.ainvoke({"messages": [HumanMessage(content=request.query)]}, config=config)

    return {
        "answer": final_state.get("answer") or final_state["messages"][-1].content,
        "is_conversational": final_state.get("is_conversational", True),
        "sources_used": final_state.get("sources_used", []),
    }


async def get_thread_messages(session_id: str) -> list:
    """Return displayable human and assistant messages from one saved graph thread."""
    async with get_compiled_app() as graph_app:
        state = await graph_app.aget_state({"configurable": {"thread_id": session_id}})

    messages = state.values.get("messages", []) if state and state.values else []
    return [
        {"role": "user" if m.type == "human" else "assistant", "content": m.content}
        for m in messages
        if m.type in ("human", "ai") and (m.content or "").strip()
    ]
"""Service layer that converts a user request into one durable graph invocation."""
