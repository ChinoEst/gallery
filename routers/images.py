from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Image, Tag
from schemas import ImageResponse, DownloadRequest
from routers.auth import verify_token
from cache import get_cache, set_cache
import aiofiles
import httpx
import asyncio
import os
import logging


#define
router = APIRouter(prefix="/images", tags=["images"])

# Semaphore restrict max download number
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(5)


#path: images/search
#type: get
#return format: list[ImageResponse]
@router.get("/search", response_model=list[ImageResponse])
async def search_images(
    tag: str = None,
    artist_id: int = None,
    payload=Depends(verify_token),
    db: AsyncSession = Depends(get_db)
    ):

    #all image with relation tags
    query = select(Image).options(selectinload(Image.tags))
    
    if artist_id and tag:
        logging.info(f"[INFO] search by artist_id: {artist_id} and tag: {tag}")
        query = query.join(Image.tags).where(Image.artist_id == artist_id).where(Tag.name == tag)

    #condition: artist_id = ?
    elif artist_id:
        logging.info(f"[INFO] search by artist_id: {artist_id}")
        query = query.where(Image.artist_id == artist_id)
    
    #condition:tag = ?
    elif tag:
        logging.info(f"[INFO] search by tag: {tag}")
        query = query.join(Image.tags).where(Tag.name == tag)


    """
    artist_id in column of image, so can search directly by where(Image.artist_id == artist_id)
    but tag is in relation table, so need to join(Image.tags) first, then search by where(Tag.name == tag)
    """

    logging.info("[INFO] searching images...")
    result = await db.execute(query)
    logging.info("[INFO] search finished!")
    return result.scalars().all()



#path: images
#type get
#return format: list[ImageResponse]
@router.get("/", response_model=list[ImageResponse])
async def get_images(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    
    logging.info("[INFO] fetching images from database...")
    result = await db.execute(
        select(Image).options(selectinload(Image.tags))
    )
    logging.info("[INFO] fetching images finished!")

    """
    select(Image).options(selectinload(Image.tags))
    |
    V
    SELECT*
    FROM images 

    info in object(image) can direct access, 
    but info in relation need to search in database again which names "lazy loading"
    which mean when you need, load it. when you doesn't, it doesn't load.
    In async can't do lazy loading and other things(connect, and so on...) at same time, so use "selectinload" to get info of image we need
    """
    return result.scalars().all()



async def download_one(image: Image, db: AsyncSession):
    #limit: DOWNLOAD_SEMAPHORE
    async with DOWNLOAD_SEMAPHORE:
        try:
            #get a request
            async with httpx.AsyncClient() as client:
                logging.info(f"[INFO] getting image {image.id} from {image.original_url}...")
                response = await client.get(image.original_url)
                logging.info(f"[INFO] image {image.id} download finished!")
                filename = f"{image.id}.jpg"
                if not os.path.exists("uploads"):
                    logging.info("[INFO] build fold: uploads")
                    os.mkdir("uploads")
                filepath = f"uploads/{filename}"
                logging.info(f"[INFO] saving image {image.id} to {filepath}...")
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                logging.info(f"[INFO] saving {image.id} to {filepath} finished!")

                #add new info to database
                image.filename = filename
                image.local_path = filepath
                image.is_downloaded = True

                logging.info(f"[INFO] updating info of image {image.id} in database...")
                await db.commit()
                logging.info(f"[INFO] info of image {image.id} updated finished!")
        except Exception as e:
            logging.error(f"[ERROR] 下載失敗 image_id={image.id}: {e}")


#path:images/download
#type:post(add)
@router.post("/download")
async def download_images(body: DownloadRequest, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    #SQL search
    logging.info(f"[INFO] checking images with ids: {body.image_ids}...")
    result = await db.execute(select(Image).where(Image.id.in_(body.image_ids)))
    logging
    images = result.scalars().all()
    if not images:
        logging.warning("[WARNING] no images found")
        raise HTTPException(status_code=404, detail="找不到圖片")
    
    #do multiple downloan at the same time, by "crazy" switch
    logging.info(f"[INFO] start downloading {len(images)} images...")
    await asyncio.gather(*[download_one(image, db) for image in images])
    logging.info("[INFO] all download tasks finished!")
    return {"message": f"下載完成，共 {len(images)} 張"}


#path: images/{image_id}
#type: get
#return format: ImageResponse
#note: /{} at bottom of others or it would cover others  @router.post("/???"")
@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    cache_key = f"image:{image_id}"
    logging.info(f"[INFO] checking cache for image_id={image_id}...")
    cached = get_cache(cache_key)
    if cached:
        logging.info(f"[INFO] cache hit: {cache_key}")
        return cached

    result = await db.execute(
        select(Image).where(Image.id == image_id).options(selectinload(Image.tags))
    )
    image = result.scalar_one_or_none()
    if not image:
        logging.warning(f"[WARNING] image_id={image_id} not found")
        raise HTTPException(status_code=404, detail="找不到此圖片")
    logging.info(f"[INFO] image_id={image_id} found in database")
    image_data = ImageResponse.model_validate(image).model_dump(mode="json")
    set_cache(cache_key, image_data, expire=300)

    return image



#path: images/{image_id}
#type: delete
#note: /{} at bottom of others or it would cover others  @router.post("/???"")
@router.delete("/{image_id}")
async def delete_image(image_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):

    logging.info(f"[INFO] checking whether image id={image_id} exists...")
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        logging.warning(f"[WARNING] image_id={image_id} not found")
        raise HTTPException(status_code=404, detail="找不到此圖片")
    logging.info(f"[INFO] image_id={image_id} found, start deleting...")
    await db.delete(image)
    logging.info(f"[INFO] image_id={image_id} delete successfully!")
    await db.commit()
    return {"message": "刪除成功"}