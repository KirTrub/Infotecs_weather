import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DB_DIR = "db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

dburl = f"sqlite+aiosqlite:///{DB_DIR}/weather.db"

engine = create_async_engine(dburl, connect_args={"check_same_thread": False})

async_session = async_sessionmaker(
    bind=engine,          
    class_=AsyncSession,   
    expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session

class Base(DeclarativeBase):
    pass