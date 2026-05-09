from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

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


#activate engine
#init all component in model
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)