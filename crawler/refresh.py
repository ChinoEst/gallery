import logging
from sqlalchemy import select   
from database import AsyncSessionLocal
from models import Artist
from crawler.base import crawl_artist




async def refresh_artists():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Artist))
        artists = result.scalars().all()
        for artist in artists:
            await crawl_artist(artist, db)
            logging.info(f"[INFO] refreshed artist_id={artist.id}, name={artist.name}")


        
        