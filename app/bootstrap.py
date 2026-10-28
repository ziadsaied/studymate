from app.clients import validate_env
from app.graph.builder import save_graph_image
from app.litellm_proxy import start_litellm_proxy, stop_litellm_proxy
from app.logging_config import logger
from app.memory.models import init_long_term_memory_db
from app.rag.ingestion import index_default_knowledge_base
from app.tracing import enable_langsmith_tracing


def startup() -> None:
    """Prepare external clients, durable storage, and the default course index."""
    enable_langsmith_tracing()
    validate_env()
    start_litellm_proxy()
    init_long_term_memory_db()
    index_default_knowledge_base()
    save_graph_image()
    logger.info("StudyMate AI backend is ready.")


def shutdown() -> None:
    """Stop the child LiteLLM process started during application startup."""
    stop_litellm_proxy()
"""Application lifecycle operations run when the FastAPI server starts and stops."""
