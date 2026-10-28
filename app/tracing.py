"""Optional LangSmith tracing setup for observing agent runs."""

import os

from app.config import LANGSMITH_PROJECT
from app.logging_config import logger


def enable_langsmith_tracing() -> None:
    """Set the environment variables LangSmith reads when instrumenting LangChain."""
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    logger.info("LangSmith tracing enabled for project '%s'.", LANGSMITH_PROJECT)
