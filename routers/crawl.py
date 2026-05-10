from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Artist
from routers.auth import verify_token
from crawler.base import crawl_artist
import asyncio

router = APIRouter(prefix="/crawl", tags=["crawl"])



##path:crawl/all/run
#type:post
@router.post("/all/run")
async def crawl_all(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    if payload["role"] != "admin":
        raise HTTPException(status_code=403, detail="權限不足")
    result = await db.execute(select(Artist))
    artists = result.scalars().all()
    await asyncio.gather(*[crawl_artist(artist, db) for artist in artists])
    return {"message": f"全部爬取完成，共 {len(artists)} 位創作者"}


#path:crawl/{artist_id}
#type:post
#note: /{} at bottom of others or it would cover others  @router.post("/???"")
@router.post("/{artist_id}")
async def crawl_one(artist_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="找不到此創作者")
    artist_name = artist.name  
    await crawl_artist(artist, db)
    return {"message": f"爬取 {artist_name} 完成"}