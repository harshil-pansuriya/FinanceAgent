from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from config.setting import Config
from config.logger import logger
import sqlalchemy.exc

engine = create_async_engine(
    Config.database_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
    connect_args={
        "server_settings": {
            "search_path": "public"
        }
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base= declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"Database connection error during init: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
async def dispose_engine():
    await engine.dispose()
    logger.info("Database engine disposed")