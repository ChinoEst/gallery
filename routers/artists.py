from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Artist
from schemas import ArtistCreate, ArtistResponse
from routers.auth import verify_token

router = APIRouter(prefix="/artists", tags=["artists"])

@router.get("/", response_model=list[ArtistResponse])
async def get_artists(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artist))
    return result.scalars().all()

@router.post("/", response_model=ArtistResponse)
async def add_artist(body: ArtistCreate, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artist).where(Artist.url == body.url))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="此創作者已存在")
    artist = Artist(name=body.name, url=body.url, platform=body.platform)
    db.add(artist)
    await db.commit()
    await db.refresh(artist)
    return artist

@router.delete("/{artist_id}")
async def delete_artist(artist_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="找不到此創作者")
    await db.delete(artist)
    await db.commit()
    return {"message": f"已刪除 {artist.name}"}