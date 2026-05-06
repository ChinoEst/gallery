import asyncio
from curl_cffi.requests import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select
from models import Artist, Image, Tag, ImageTag

CRAWL_SEMAPHORE = asyncio.Semaphore(3)

async def get_or_create_tag(db: DBSession, tag_name: str) -> Tag:
    result = await db.execute(select(Tag).where(Tag.name == tag_name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.flush()
    return tag

async def crawl_project(client, hash_id: str, artist: Artist, db: DBSession):
    async with CRAWL_SEMAPHORE:
        try:
            res = await client.get(f"https://www.artstation.com/projects/{hash_id}.json")
            data = res.json()

            tags = [c["name"] for c in data.get("categories", [])]
            cover_url = data.get("cover_url")

            for asset in data.get("assets", []):
                if not asset.get("has_image"):
                    continue

                image_url = asset.get("image_url")

                result = await db.execute(select(Image).where(Image.original_url == image_url))
                if result.scalar_one_or_none():
                    continue

                image = Image(
                    artist_id=artist.id,
                    original_url=image_url,
                    thumbnail_url=cover_url,
                )
                db.add(image)
                await db.flush()

                for tag_name in tags:
                    tag = await get_or_create_tag(db, tag_name)
                    db.add(ImageTag(image_id=image.id, tag_id=tag.id))

            await db.commit()

        except Exception as e:
            await db.rollback()
            print(f"爬取失敗 hash_id={hash_id}: {e}")

async def crawl_artstation(artist: Artist, db: AsyncSession):
    username = artist.url.rstrip("/").split("/")[-1]
    artist_name = artist.name
    print(f"開始爬取 ArtStation: {username}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with AsyncSession(impersonate="chrome") as client:
        res = await client.get(f"https://www.artstation.com/users/{username}/projects.json")
        print(f"HTTP 狀態: {res.status_code}")
        data = res.json()
        projects = data.get("data", [])
        print(f"抓到 {len(projects)} 個作品")
        for p in projects:
            await crawl_project(client, p["hash_id"], artist, db)
    print(f"ArtStation 爬取完成: {artist_name}，共 {len(projects)} 個作品")