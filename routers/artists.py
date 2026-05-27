from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Artist, Image
from schemas import ArtistCreate, ArtistResponse, ArtistDetailResponse
from routers.auth import verify_token
import logging

#define
router = APIRouter(prefix="/artists", tags=["artists"])




#path: artists
#method: get
#return format: list[ArtistResponse]
@router.get("/", response_model=list[ArtistResponse])
async def get_artists(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    #search by SQL
    logging.info("[INFO] fetching artists from database...")
    result = await db.execute(select(Artist))

    #take all data
    logging.info("[INFO] Successful!")
    return result.scalars().all()


#path: artists
#method: post(add)
#return format: ArtistResponse
@router.post("/", response_model=ArtistResponse)
async def add_artist(body: ArtistCreate, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    #search by SQL
    logging.info("[INFO] checking whether artist exists...")
    result = await db.execute(select(Artist).where(Artist.url == body.url))
    if result.scalar_one_or_none():
        logging.warning("[WARNING] artist already exists")
        raise HTTPException(status_code=400, detail="此創作者已存在")
    
    #add new object(artist)
    artist = Artist(name=body.name, url=body.url, platform=body.platform)
    logging.info(f"[INFO] artist {artist.name} created successfully!")
    db.add(artist)
    await db.commit()
    logging.info(f"[INFO] artist {artist.name} add to database successfully!")
    await db.refresh(artist)
    logging.info(f"[INFO] database refreshed")
    """
    need object.id do refresh:

    process on get artist.id:
    db.add(artist)->waiting list.append()
    await db.commit() -> updata to database,  note: python doesn't know it!
    await db.refresh(artist) refresh and get artist_id
    """
    return artist


@router.get("/artist/{name}", response_model=ArtistDetailResponse)
async def artist_detail(name: str, payload = Depends(verify_token), db: AsyncSession = Depends(get_db)):

    logging.info("[INFO] fetching artist detail from database...")
    result = await db.execute(select(Artist).where(Artist.name == name))
    artist = result.scalar_one_or_none()
    if not artist:
        logging.warning(f"[WARNING] artist not found")
        raise HTTPException(status_code=404, detail="找不到此創作者")
    
    logging.info("[INFO] artist found, fetching image count...")
    Len = await db.execute(select(func.count()).select_from(Image).join(Artist).where(Artist.name == name))
    Len = Len.scalar_one()
    logging.info(f"[INFO] image count for artist name={artist.name} is {Len}")

    return ArtistDetailResponse(
        id=artist.id,
        name=artist.name,
        url=artist.url,
        platform=artist.platform,
        created_at=artist.created_at,
        image_count=Len
    )


    


#path: artists/{artist_id}
#type: delete
@router.delete("/{artist_id}")
async def delete_artist(artist_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    logging.info(f"[INFO] checking whether artist id={artist_id} exists...")
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        logging.warning("[WARNING] artist not found")
        raise HTTPException(status_code=404, detail="找不到此創作者")
    await db.delete(artist)
    logging.info(f"[INFO] artist {artist.name} delete successfully!")
    await db.commit()
    """
    not need id ,don't refresh
    """
    return {"message": f"已刪除 {artist.name}"}



