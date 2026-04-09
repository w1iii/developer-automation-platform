import os
from typing import AsyncGenerator

from sqlalchemy import create_async_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Database url is not set in .env")
print("Database URL: ", DATABASE_URL)
engine = create_async_engine(
    DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True
)
AsyncSessionLocal = sessionmaker(bind=engine, class=AsyncSession, expire_on_commit=False, async_engine=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionLocal()
    try:
        yield db
    except Exception as e:
        print("Database error: ", e)
        raise
    finally:
        db.close()
