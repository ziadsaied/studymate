from contextlib import asynccontextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.config import CHECKPOINT_DB_PATH
from app.logging_config import logger
from app.graph.nodes import (
    call_agent,
    check_cache,
    finalize,
    route_after_agent,
    route_after_cache,
    route_after_finalize,
    summarize_memory,
)
from app.schemas import AgentState
from app.tools.registry import research_tools

GRAPH_IMAGE_PATH = Path(__file__).resolve().parents[2] / "compiled_graph.png"


def build_graph() -> StateGraph:
    """Create the routing graph without opening its SQLite checkpoint connection."""
    workflow = StateGraph(AgentState)

    # Nodes either inspect state, call the model, run model-selected tools, or finish a turn.
    workflow.add_node("check_cache", check_cache)
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", ToolNode(research_tools))
    workflow.add_node("finalize", finalize)
    workflow.add_node("summarize", summarize_memory)

    # Every incoming message first gets a cheap exact-question cache lookup.
    workflow.add_edge(START, "check_cache")

    workflow.add_conditional_edges("check_cache", route_after_cache, {
        "agent": "agent",
        "summarize": "summarize",
        END: END,
    })

    workflow.add_conditional_edges("agent", route_after_agent, {
        "tools": "tools",
        "finalize": "finalize",
    })

    # Tool results are appended to state, then returned to the model for synthesis.
    workflow.add_edge("tools", "agent")

    workflow.add_conditional_edges("finalize", route_after_finalize, {
        "summarize": "summarize",
        END: END,
    })

    workflow.add_edge("summarize", END)

    return workflow


def _save_graph_image(compiled_graph) -> None:
    """Save the compiled graph visualization once for the current project."""
    if GRAPH_IMAGE_PATH.exists():
        return

    try:
        compiled_graph.get_graph().draw_mermaid_png(
            output_file_path=str(GRAPH_IMAGE_PATH),
        )
        logger.info("Compiled graph image saved to %s", GRAPH_IMAGE_PATH)
    except Exception:
        logger.exception("Could not save compiled graph image")


def save_graph_image() -> None:
    """Compile the workflow without checkpoints and save its visualization."""
    _save_graph_image(build_graph().compile())


@asynccontextmanager
async def get_compiled_app():
    """Yield a compiled graph backed by SQLite conversation checkpoints."""
    # A context manager ensures the async SQLite connection closes after each request.
    async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB_PATH) as memory:
        compiled_graph = build_graph().compile(checkpointer=memory)
        _save_graph_image(compiled_graph)
        yield compiled_graph
"""Assemble the LangGraph workflow that powers one StudyMate conversation."""
