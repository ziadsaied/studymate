import asyncio
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.memory.store import (
    get_or_create_user_by_name,
    get_thread_owner,
    get_user_profile,
    get_user_sidebar_history,
    list_users,
    user_owns_thread,
)
from app.rag.ingestion import add_uploaded_pdf
from app.service import get_thread_messages, run_agentic_rag

router = APIRouter()

# Uploaded PDFs are retained locally so they can be re-indexed after a restart.
UPLOAD_DIR = Path("uploaded_material")
UPLOAD_DIR.mkdir(exist_ok=True)


class ChatRequest(BaseModel):
    """Small browser-facing request shape, translated to UserRequest by the service."""
    message: str
    thread_id: str
    user_id: str


class UserRequest(BaseModel):
    """A local profile needs only a human-readable name, never a password."""

    username: str = Field(min_length=1, max_length=50)


@router.get("/users")
async def users():
    """List locally registered profiles for the account switcher."""
    return await asyncio.to_thread(list_users)


@router.post("/users")
async def create_user(payload: UserRequest):
    """Register a profile or select its existing case-insensitive match."""
    try:
        return await asyncio.to_thread(get_or_create_user_by_name, payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/threads")
async def list_threads(user_id: str = Query(min_length=1)):
    """Return sidebar metadata for one selected local profile."""
    if not await asyncio.to_thread(get_user_profile, user_id):
        raise HTTPException(status_code=404, detail="User profile not found.")
    threads = await asyncio.to_thread(get_user_sidebar_history, user_id)
    return [{"thread_id": t["thread_id"], "title": t["title"]} for t in threads]


@router.get("/threads/{thread_id}/messages")
async def thread_messages(thread_id: str, user_id: str = Query(min_length=1)):
    """Return the selected conversation's displayable checkpoint messages."""
    owns_thread = await asyncio.to_thread(user_owns_thread, user_id, thread_id)
    if not owns_thread:
        raise HTTPException(status_code=404, detail="Conversation not found for this user.")
    return await get_thread_messages(thread_id)


@router.post("/chat")
async def chat(payload: ChatRequest):
    """Run one agent turn and return its final answer to the browser."""
    if not await asyncio.to_thread(get_user_profile, payload.user_id):
        raise HTTPException(status_code=404, detail="User profile not found.")
    thread_owner = await asyncio.to_thread(get_thread_owner, payload.thread_id)
    if thread_owner and thread_owner != payload.user_id:
        raise HTTPException(status_code=403, detail="This conversation belongs to another user.")
    result = await run_agentic_rag(
        {"query": payload.message, "session_id": payload.thread_id, "user_id": payload.user_id}
    )
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Save an uploaded PDF locally, then add its chunks to the vector store."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    destination = UPLOAD_DIR / file.filename
    # Stream the upload to disk instead of reading the entire PDF into memory first.
    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        await asyncio.to_thread(add_uploaded_pdf, str(destination))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not index '{file.filename}': {exc}") from exc

    return {"filename": file.filename, "status": "indexed"}
"""HTTP endpoints used by the browser chat interface."""
