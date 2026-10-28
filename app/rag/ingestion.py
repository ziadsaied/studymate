from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.indexing import index
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import DEFAULT_KB_PATH
from app.logging_config import logger
from app.rag.retriever import record_manager, vectorstore


def load_and_split_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 150):
    """Extract PDF pages and make overlapping chunks for semantic retrieval."""
    pages = PyMuPDFLoader(pdf_path).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(pages)
    logger.info("Split '%s' into %d chunk(s).", pdf_path, len(chunks))
    return chunks


def index_document(pdf_path: str) -> dict:
    """Index one PDF incrementally, preserving unchanged chunks already in Chroma."""
    chunks = load_and_split_pdf(pdf_path)
    logger.info("Indexing '%s' (%d chunk(s)) into the shared knowledge base...", pdf_path, len(chunks))
    result = index(
        chunks,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="source",
    )
    logger.info("Indexing result for '%s': %s", pdf_path, result)
    return result


def add_uploaded_pdf(pdf_path: str) -> dict:
    """Validate and index a PDF supplied through the upload endpoint."""
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"Uploaded file not found: {pdf_path}")
    logger.info("Processing student-uploaded PDF: '%s'", pdf_path)
    result = index_document(pdf_path)
    logger.info("'%s' processed and added to StudyMate's knowledge base: %s", Path(pdf_path).name, result)
    return result


def index_default_knowledge_base() -> Optional[dict]:
    """Index the bundled course PDF when it is available at startup."""
    if not Path(DEFAULT_KB_PATH).exists():
        logger.warning("'%s' was not found -- skipping default knowledge base indexing.", DEFAULT_KB_PATH)
        return None
    return index_document(DEFAULT_KB_PATH)
"""Load PDFs, split them into chunks, and index them in the shared vector store."""
