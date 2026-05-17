from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging

#sqlite:dataset type
#aiosqlite:drive version
#save in gallery.db
DATABASE_URL = "sqlite+aiosqlite:///./gallery.db"


#build database
engine = create_async_engine(DATABASE_URL, echo=True)
"""
engine:
    for maintain connect
    do command from session

session:
    communiate between engine and user
"""


#generate session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


#get session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
    logging.info("[INFO] session end.")


#activate engine
#init all component in model
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("[INFO] Database initialized.")


"""
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
only for routers use, get session, end session after router end, not for other use.

other function get session:
async with AsyncSessionLocal() as session:
    do something    
    logging.info("[INFO] session end.")

sesseion expire is only for commit, after commit database update, but session still have old data, so we need to refresh to get new.

There is no relation between session end and expire, session end is for release resource, expire is for data update.


"""