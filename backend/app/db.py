import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "dhruv1104")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "pm_intern_alloc")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# Async MySQL URL
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True, future=True)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

if __name__ == "__main__":
    import asyncio

    async def test_connection():
        try:
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            print("✅ Database connection successful!")
        except Exception as e:
            print("❌ Database connection failed:", e)

    asyncio.run(test_connection())