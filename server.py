from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from routers import auth, artists, images, crawl
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("gallery")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("初始化資料庫")
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(artists.router)
app.include_router(images.router)
app.include_router(crawl.router)

#CORS set
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)