from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Artist
from routers.auth import verify_token
from crawler.base import crawl_artist
import asyncio
import logging

router = APIRouter(prefix="/crawl", tags=["crawl"])



##path:crawl/all/run
#type:post
@router.post("/all/run")
async def crawl_all(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    if payload["role"] != "admin":
        logging.warning(f"[WARNING] user {payload['sub']} with role {payload['role']} tried to crawl all artists")
        raise HTTPException(status_code=403, detail="權限不足")
    logging.info(f"[INFO] user {payload['sub']} with role {payload['role']} is crawling all artists...")
    result = await db.execute(select(Artist))
    artists = result.scalars().all()
    logging.info(f"[INFO] {len(artists)} artists found in database, start crawling...")
    await asyncio.gather(*[crawl_artist(artist, db) for artist in artists])
    logging.info(f"[INFO] all crawl tasks finished!")
    return {"message": f"全部爬取完成，共 {len(artists)} 位創作者"}


#path:crawl/{artist_id}
#type:post
#note: /{} at bottom of others or it would cover others  @router.post("/???"")
@router.post("/{artist_id}")
async def crawl_one(artist_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    logging.info(f"[INFO] checking whether artist id={artist_id} exists...")
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        logging.warning(f"[WARNING] artist_id={artist_id} not found")
        raise HTTPException(status_code=404, detail="找不到此創作者")
    artist_name = artist.name
    logging.info(f"[INFO] artist_id={artist_id} found, start crawling...")
    await crawl_artist(artist)
    logging.info(f"[INFO] crawling of artist_id={artist_id} finished!")
    return {"message": f"爬取 {artist_name} 完成"}