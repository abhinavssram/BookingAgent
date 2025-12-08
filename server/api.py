from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.endpoints import router
from server.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before the application starts
    init_db()
    yield
    # Shutdown: runs after the application stops (add cleanup here if needed)

app = FastAPI(lifespan=lifespan)

app.include_router(router)