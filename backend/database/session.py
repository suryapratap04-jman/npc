import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = settings.computed_database_url
logger.info(f"Connecting to database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True, # automatic connection verification to handle restarts
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for yielding database session contexts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
