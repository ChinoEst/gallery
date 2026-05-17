import asyncio
from database import AsyncSessionLocal
from sqlalchemy import delete
from models import Image, ImageTag
import logging

async def main():
    async with AsyncSessionLocal() as db:
        logging.info("[INFO] Starting to clear database...")
        await db.execute(delete(ImageTag))
        await db.execute(delete(Image))
        await db.commit()
        logging.info("[INFO] Database cleared successfully!")
        print("清除完成")

asyncio.run(main())