from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.bootstrap import shutdown, startup

# Resolve from this source file so the app works regardless of the shell's directory.
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run project startup before accepting requests, then clean up on shutdown."""
    startup()
    yield
    shutdown()


app = FastAPI(title="StudyMate AI", lifespan=lifespan)

# Keep JSON endpoints under /api while serving the plain browser UI at the root.
app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_ui():
    """Return the one-page chat application."""
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )
"""FastAPI application setup, static-file hosting, and lifecycle integration."""
