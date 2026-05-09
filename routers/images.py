from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Image
from schemas import ImageResponse, DownloadRequest
from routers.auth import verify_token
import aiofiles
import httpx
import asyncio

#define
router = APIRouter(prefix="/images", tags=["images"])

# Semaphore restrict max download number
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(5)




#path: images
#type get
#return format: list[ImageResponse]
@router.get("/", response_model=list[ImageResponse])
async def get_images(payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Image).options(selectinload(Image.tags))
    )
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



#path: images/{image_id}
#type: get
#return format: ImageResponse
@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Image).where(Image.id == image_id).options(selectinload(Image.tags))
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="找不到此圖片")
    return image


#path: images/{image_id}
#type: delete
@router.delete("/{image_id}")
async def delete_image(image_id: int, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="找不到此圖片")
    await db.delete(image)
    await db.commit()
    return {"message": "刪除成功"}



async def download_one(image: Image, db: AsyncSession):
    #limit: DOWNLOAD_SEMAPHORE
    async with DOWNLOAD_SEMAPHORE:
        try:
            #get a request
            async with httpx.AsyncClient() as client:
                response = await client.get(image.original_url)
                filename = f"{image.id}.jpg"
                filepath = f"uploads/{filename}"
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                image.filename = filename
                image.local_path = filepath
                image.is_downloaded = True
                await db.commit()
        except Exception as e:
            print(f"下載失敗 image_id={image.id}: {e}")


#path:images/download
#type:post(add)
@router.post("/download")
async def download_images(body: DownloadRequest, payload=Depends(verify_token), db: AsyncSession = Depends(get_db)):
    #SQL search
    result = await db.execute(select(Image).where(Image.id.in_(body.image_ids)))
    images = result.scalars().all()
    if not images:
        raise HTTPException(status_code=404, detail="找不到圖片")
    
    #do multiple downloan at the same time, by "crazy" switch
    await asyncio.gather(*[download_one(image, db) for image in images])
    return {"message": f"下載完成，共 {len(images)} 張"}