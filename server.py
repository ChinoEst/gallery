from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from routers import auth
from routers import artists


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(artists.router)