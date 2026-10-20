"""Shared fixtures.

Tests run against in-memory SQLite rather than Postgres.  That is possible only
because registry.db builds its engine lazily -- importing crud no longer opens a
connection, so a test can supply its own engine.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from registry.db import Base

# Importing models is what registers Model/Version/DeploymentRecord on Base.
# Without it, create_all() would find no tables to create.
from registry import models  # noqa: F401


@pytest.fixture
def db():
    """A session against a fresh, empty database.

    Each test gets its own engine, so no state leaks between tests.
    """
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
