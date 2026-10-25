from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_db_engine() -> Engine:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    url = settings.database_url
    if ".redshift.amazonaws.com" in url:
        # The PostgreSQL dialect cannot initialise against Redshift; use the Redshift one
        url = url.replace("postgresql+psycopg://", "redshift+redshift_connector://").split("?")[0]
    return create_engine(url, pool_pre_ping=True)


engine = create_db_engine() if settings.database_url else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


def get_session() -> Iterator[Session]:
    if SessionLocal is None:
        raise RuntimeError("Database session is unavailable because DATABASE_URL is empty")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

