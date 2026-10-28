"""Local development entry point for the StudyMate FastAPI server."""

import threading
import webbrowser

import uvicorn

if __name__ == "__main__":
    # The application lifespan hook starts supporting services before serving requests.
    threading.Timer(1.0, webbrowser.open, args=("http://127.0.0.1:8000",)).start()
    uvicorn.run("app.api.server:app", host="127.0.0.1", port=8000, reload=False)
