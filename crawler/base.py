from models import Artist
from sqlalchemy.ext.asyncio import AsyncSession
from crawler.artstation import crawl_artstation

async def crawl_artist(artist: Artist, db: AsyncSession):
    if artist.platform.lower() == "artstation":
        await crawl_artstation(artist, db)
    else:
        print(f"不支援的平台: {artist.platform}")