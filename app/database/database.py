from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.setting import Config
from config.logger import logger
import sqlalchemy.exc

engine = create_async_engine(
    Config.database_url,
    pool_size=15,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=False,
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
            # Check if tables exist before creating
            existing_tables = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )
            if not all(table in existing_tables for table in ['users', 'transactions', 'user_preferences']):
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
            else:
                logger.info("Database tables already exist")
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"Database connection error during init: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
async def dispose_engine():
    await engine.dispose()
    logger.info("Database engine disposed")