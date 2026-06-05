import asyncio
from curl_cffi.requests import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select
from models import Artist, Image, Tag, ImageTag
import logging
from database import AsyncSessionLocal

CRAWL_SEMAPHORE = asyncio.Semaphore(3)

async def get_or_create_tag(db: DBSession, tag_name: str) -> Tag:

    logging.info(f"[INFO] checking whether tag '{tag_name}' exists...")
    result = await db.execute(select(Tag).where(Tag.name == tag_name))
    tag = result.scalar_one_or_none()
    if not tag:
        logging.info(f"[INFO] tag '{tag_name}' not found, creating new tag...")
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.flush()
        logging.info(f"[INFO] tag '{tag_name}' created with id={tag.id}")
    return tag


async def crawl_project(client, hash_id: str, artist: Artist):
    async with CRAWL_SEMAPHORE:
        async with AsyncSessionLocal() as session:
            try:
                logging.info(f"[INFO] crawling project hash_id={hash_id} for artist_id={artist.id}...")
                #get url from site for database
                res = await client.get(f"https://www.artstation.com/projects/{hash_id}.json")
                logging.info(f"[INFO] HTTP status for project hash_id={hash_id}: {res.status_code}")
                data = res.json()

                #access all tag with all images from  artist
                logging.debug(f"[DEBUG] project data for hash_id={hash_id}: {data}")
                tags = [c["name"] for c in data.get("categories", [])]
                cover_url = data.get("cover_url")

                # access the first
                first_image = None
                logging.debug(f"[DEBUG] checking assets for hash_id={hash_id}")
                for asset in data.get("assets", []):
                    if asset.get("has_image"):
                        first_image = asset.get("image_url")
                        break

                if not first_image:
                    logging.warning(f"[WARNING] no valid image found for project hash_id={hash_id}")
                    return

                # 檢查是否已存在
                logging.info(f"[INFO] checking whether image for project hash_id={hash_id} exists...")
                result = await session.execute(select(Image).where(Image.original_url == first_image))
                if result.scalar_one_or_none():
                    logging.info(f"[INFO] image for project hash_id={hash_id} already exists.")
                    return

                image = Image(
                    artist_id=artist.id,
                    original_url=first_image,
                    thumbnail_url=cover_url,
                )
                session.add(image)
                
                """
                    add   -> flush -> commit -> refresh
                register    send     updata     sync

                flush: getimage.id before updata

                Note: after commit, session expored, need refresh to get new id
                """
                await session.flush()

                for tag_name in tags:
                    tag = await get_or_create_tag(session, tag_name)
                    session.add(ImageTag(image_id=image.id, tag_id=tag.id))
                logging.info(f"[INFO] project hash_id={hash_id} crawl successfully, image_id={image.id} created with {len(tags)} tags.")
                await session.commit()
                logging.info(f"[INFO] project hash_id={hash_id} committed to database successfully!")

            except Exception as e:
                #restore all changes if crawl failed
                await session.rollback()
                logging.error("[ERROR] database rollback due to crawl failure")
                logging.error(f"[ERROR] 爬取失敗 hash_id={hash_id}: {e}")



async def crawl_artstation(artist: Artist):##
    username = artist.url.rstrip("/").split("/")[-1]
    artist_name = artist.name
    logging.info(f"[INFO] starting crawl for ArtStation user: {username}")

    #pretend a browser to avoid being blocked
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    logging.debug(f"[DEBUG] using headers: {headers}")
    async with AsyncSession(impersonate="chrome") as client:
        res = await client.get(f"https://www.artstation.com/users/{username}/projects.json")
        logging.info(f"[INFO] HTTP status for user {username}: {res.status_code}")
        data = res.json()
        projects = data.get("data", [])
        logging.info(f"[INFO] found {len(projects)} projects for user {username}")
        for p in projects:
            await crawl_project(client, p["hash_id"], artist)

        """
        asyncio.gather ->use same session at the same time -> cause session conflict
        for p in projects:
            await crawl_project(client, p["hash_id"], artist, db)
        -> still use same session but not at the same time, because of semaphore, but it will be slower

        another way:
        async with AsyncSession(impersonate="chrome") as client:
            for p in projects:
                await crawl_project(client, p["hash_id"], artist_id)

         def crawl_project(client, hash_id, artist_id):
            async with AsyncSession() as db:
                do something
        
        defected because of too many session create and close, but it will be faster
        i resort stable way, one after one.
                

        """
    logging.info(f"[INFO] ArtStation crawl completed for user: {artist_name}, total projects: {len(projects)}")
