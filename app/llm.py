"""Expose LangChain chat clients that talk to the local LiteLLM router."""

from langchain_openai import ChatOpenAI

from app.config import LITELLM_BASE_URL
from app.logging_config import logger

# The agent pool may route requests across multiple configured providers.
agent_llm = ChatOpenAI(
    model="agent-pool",
    base_url=LITELLM_BASE_URL,
    api_key="anything",
    temperature=0,
)

# Summarization has its own model alias so it can be cheaper or more specialized.
summary_llm = ChatOpenAI(
    model="summary-pool",
    base_url=LITELLM_BASE_URL,
    api_key="anything",
    temperature=0,
)

logger.info(
    "LLMs initialized via LiteLLM proxy: agent_llm -> 'agent-pool' (2 models), "
    "summary_llm -> 'summary-pool' (1 model)."
)
