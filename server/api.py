from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.endpoints import router
from server.db.database import init_db
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before the application starts
    init_db()
    yield
    # Shutdown: runs after the application stops (add cleanup here if needed)

app = FastAPI(lifespan=lifespan)

app.include_router(router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))