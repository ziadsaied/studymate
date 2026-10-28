from langchain_chroma import Chroma
from langchain_classic.indexes import SQLRecordManager
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, RECORD_MANAGER_DB_URL
from app.logging_config import logger

# Normalized embeddings make cosine similarity comparable across document chunks.
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)
logger.info("Embedding model ready: BAAI/bge-m3 (normalized embeddings, local).")

# Chroma persists vectors on disk so uploaded and default documents survive restarts.
vectorstore = Chroma(
    collection_name=CHROMA_COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_PERSIST_DIR,
    collection_metadata={"hnsw:space": "cosine"},
)
logger.info("Chroma vector store ready: collection='%s' (HNSW, cosine).", CHROMA_COLLECTION_NAME)

# The record manager tracks indexed source chunks and avoids duplicate indexing work.
record_manager = SQLRecordManager(
    namespace=f"chroma/{CHROMA_COLLECTION_NAME}",
    db_url=RECORD_MANAGER_DB_URL,
)
record_manager.create_schema()
logger.info("Record manager schema ready (namespace='chroma/%s').", CHROMA_COLLECTION_NAME)

# MMR returns relevant chunks while encouraging diversity rather than near-duplicates.
global_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 2,
        "fetch_k": 10,
        "lambda_mult": 0.5,
    },
)
logger.info("Retriever ready: MMR (k=2, fetch_k=10) -> global_retriever.")
"""Initialize the embedding model, persistent Chroma store, and document retriever."""
