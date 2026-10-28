# StudyMate AI

Agentic RAG study assistant: LangGraph + LiteLLM (Groq) + Chroma + SQLAlchemy long-term memory.

## Structure

- `app/config.py`, `app/logging_config.py` - settings and logging.
- `app/tracing.py`, `app/clients.py`, `app/litellm_proxy.py`, `app/llm.py` - external services (LangSmith, SerpAPI, LiteLLM proxy, LLM clients).
- `app/schemas.py`, `app/prompts.py` - shared state/schemas and the system prompt.
- `app/rag/` - PDF ingestion, embeddings, Chroma vector store, retriever.
- `app/memory/` - SQLAlchemy models and long-term memory (student preferences, thread sidebar).
- `app/tools/` - LangGraph tools (web search, define term, RAG retrieval, memory, final answer) and tool registry.
- `app/graph/` - LangGraph nodes and graph assembly (`build_graph`, `get_compiled_app`).
- `app/service.py` - `run_agentic_rag`, the single entry point a UI layer calls.
- `app/bootstrap.py` - `startup()` / `shutdown()`: starts the LiteLLM proxy, inits the long-term memory DB, indexes the default knowledge base.
- `scripts/demo.py` - CLI demo, equivalent to the original notebook's test cells.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in the keys.
3. Put `config.yaml` (LiteLLM proxy config) and `Data Analysis Basics.pdf` (default knowledge base) next to this README.
4. `python scripts/demo.py` to sanity-check the pipeline end to end.

## Running the app

```
python main.py
```

Then open `http://127.0.0.1:8000`. This starts the FastAPI server (`app/api/server.py`), which on
startup also starts the LiteLLM proxy, initializes the long-term memory DB, and indexes the default
knowledge base (same as `app.bootstrap.startup()`).

## FastAPI layer

- `app/api/server.py` - app factory, lifespan (`startup`/`shutdown`), mounts `static/` and serves `index.html` at `/`.
- `app/api/routes.py` - `GET /api/threads`, `GET /api/threads/{id}/messages`, `POST /api/chat`, `POST /api/upload`.
- `static/` - the chat UI (sidebar with past conversations, chat pane, PDF upload). Plain HTML/CSS/JS, no build step.
- This is a single-user app (`DEFAULT_USER_ID` in `app/config.py`); every thread belongs to that one user, which is what the sidebar lists.
