from langchain_core.tools import tool

from app.logging_config import logger
from app.rag.retriever import global_retriever
from app.schemas import RetrieveInternalDocsInput


@tool(args_schema=RetrieveInternalDocsInput, response_format="content_and_artifact")
async def retrieve_internal_documents(query: str) -> tuple:
    """
    Performs semantic search and retrieval from the local vector database (the
    default course knowledge base plus any PDFs the student has uploaded).

    USE THIS TOOL ONLY WHEN:
    - The student asks for NEW factual, technical, or domain-specific information
      that has NOT been discussed yet.

    DO NOT USE THIS TOOL WHEN:
    - The user input is conversational (greetings, pleasantries).
    - The exact information needed to answer the question is ALREADY present in
      the recent chat history.
    """
    try:
        logger.info("Tool called: retrieve_internal_documents | query='%s'", query)
        # Retrieval runs asynchronously because embedding/vector-store work may take time.
        docs = await global_retriever.ainvoke(query)

        if not docs:
            logger.warning("No documents found for query: '%s'", query)
            return "No relevant documents found in the database.", []

        formatted_docs = []
        sources = []
        # Return readable evidence to the model and structured source labels to the UI.
        for doc in docs:
            source = doc.metadata.get("source", "Unknown Document")
            page = doc.metadata.get("page", "Unknown")
            formatted_docs.append(f"[Source: {source} | Page: {page}]\nContent: {doc.page_content}")
            sources.append(f"{source} (page {page})")

        logger.info("retrieve_internal_documents returned %d chunk(s) for query: '%s'", len(formatted_docs), query)
        return "\n\n---\n\n".join(formatted_docs), list(dict.fromkeys(sources))

    except Exception:
        logger.exception("Error inside retrieve_internal_documents tool.")
        return "Error during retrieval. Use fallback knowledge if explicitly asked, otherwise state you don't know.", []
"""Tool for retrieving evidence from the locally indexed course PDFs."""
