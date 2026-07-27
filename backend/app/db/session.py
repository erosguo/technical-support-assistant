from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def _get_engine():
    dsn = settings.db_dsn.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(dsn, echo=settings.debug)


_engine = None
_session_local = None


def get_session() -> Session:
    global _engine, _session_local
    if _engine is None:
        _engine = _get_engine()
        _session_local = sessionmaker(bind=_engine)
    session = _session_local()
    try:
        yield session
    finally:
        session.close()
