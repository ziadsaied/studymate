import asyncio

import httpx
from langchain_core.tools import tool

from app.clients import search_client
from app.logging_config import logger


@tool
async def web_search(query: str) -> str:
    """
    Search the web using Google and return relevant search results.
    Use this tool when the student asks for current information,
    facts that may have changed, or information that requires web search.
    """
    logger.info("Tool called: web_search | query='%s'", query)

    try:
        # SerpAPI's client is synchronous, so offload it to avoid blocking the event loop.
        results = await asyncio.to_thread(
            search_client.search, {"engine": "google", "q": query}
        )
    except Exception:
        logger.exception("Error inside web_search tool.")
        return "Web search failed. Use fallback knowledge if explicitly asked, otherwise state you don't know."

    organic_results = results.get("organic_results", [])

    if not organic_results:
        logger.warning("web_search returned no results for query: '%s'", query)
        return "No search results found."

    output = []
    for result in organic_results[:2]:
        title = result.get("title", "")
        snippet = result.get("snippet", "")[:220]
        link = result.get("link", "")
        output.append(
            f"Title: {title}\n"
            f"Snippet: {snippet}\n"
            f"Link: {link}"
        )

    logger.info("web_search returned %d result(s) for query: '%s'", len(output), query)
    return "\n\n".join(output)


@tool
async def define_term(term: str) -> str:
    """
    Look up a short, reliable definition/summary of an academic term or concept
    from Wikipedia. Use this when the student asks 'what is X' / 'define X' / 'I need to know X' / 'I don't understant X'
    for a concept you're not fully sure about.
    """
    logger.info("Tool called: define_term | term='%s'", term)

    try:
        # A short timeout keeps an unavailable external service from stalling the whole chat.
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{term.replace(' ', '_')}"
            )
    except Exception:
        logger.exception("Error inside define_term tool.")
        return f"Could not reach Wikipedia to define '{term}'."

    if response.status_code != 200:
        logger.warning("define_term: no definition found for '%s' (status %s)", term, response.status_code)
        return f"No definition found for '{term}'."

    data = response.json()
    extract = data.get("extract")

    if not extract:
        logger.warning("define_term: empty extract for '%s'", term)
        return f"No definition found for '{term}'."

    logger.info("define_term succeeded for '%s'", term)
    return extract
"""Tools for web search and concise academic definitions."""
