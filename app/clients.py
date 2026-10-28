"""Construct lightweight clients for external services used by tools."""

import os

import serpapi

from app.config import REQUIRED_ENV_KEYS
from app.logging_config import logger

# The web-search tool reuses one configured SerpAPI client for every request.
search_client = serpapi.Client(api_key=os.environ["SERPAPI_KEY"])


def validate_env() -> None:
    """Log missing model credentials before LiteLLM attempts to use them."""
    missing = [k for k in REQUIRED_ENV_KEYS if not os.getenv(k)]
    if missing:
        logger.warning(
            "Missing keys in .env: %s -- the matching model_list entries in "
            "config.yaml will fail to start.", missing,
        )
    else:
        logger.info("Environment check complete. Required model keys (%s) present.", REQUIRED_ENV_KEYS)
