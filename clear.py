import asyncio
from database import AsyncSessionLocal
from sqlalchemy import delete
from models import Image, ImageTag

async def main():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(ImageTag))
        await db.execute(delete(Image))
        await db.commit()
        print("清除完成")

asyncio.run(main())