from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

from common.a2a_server import create_app
from .task_manager import run

app = create_app(agent=type("Agent", (), {"execute": run}))
@app.get("/")
async def root():
    return {"status": "ok", "service": "flight-agent"}

# Mount .well-known for agent discovery (A2A)
try:
    from fastapi.staticfiles import StaticFiles
    import pathlib
    WELL_KNOWN_DIR = pathlib.Path(__file__).parent / ".well-known"
    if WELL_KNOWN_DIR.is_dir():
        app.mount("/.well-known", StaticFiles(directory=str(WELL_KNOWN_DIR)), name="well-known")
except ImportError:
    pass  # If not FastAPI or StaticFiles not available, skip mounting

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8001)
