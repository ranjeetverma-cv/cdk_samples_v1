from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

from common.a2a_server import create_app
from .agent import execute
# from .task_manager import run
# app = create_app(agent=type("Agent", (), {"execute": run}))

app = create_app(agent=type("Agent", (), {"execute": execute}))
# Add a root endpoint for health checks
@app.get("/")
async def root():
    return {"status": "ok", "service": "host-agent"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)