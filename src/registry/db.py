"""Database engine, session factory, and the FastAPI session dependency.

The engine is built lazily so that importing this module (and therefore the
whole ``registry`` package) never requires a reachable database.  That keeps
``models``/``crud`` importable in tests, which supply their own engine.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Driver is pinned explicitly: a bare "postgresql://" URL resolves to psycopg2
# on SQLAlchemy 2.0 but to psycopg (v3) on 2.1+, so leaving it off makes the
# connection depend on which SQLAlchemy happens to be installed.
DEFAULT_DATABASE_URL = "postgresql+psycopg2://registry:registry@localhost:5432/registry"

# Declarative base needs no connection, so it stays at module level -- models.py
# and alembic/env.py both import it without touching a database.
Base = declarative_base()

_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Connection string, overridable with the DATABASE_URL environment variable."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine():
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), echo=False)
    return _engine


def get_session_factory():
    """Return the process-wide sessionmaker, creating it on first use."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False)
    return _SessionLocal


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
