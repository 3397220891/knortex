import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from celery_app import celery_app
from db import models  # noqa: F401  (registers ORM models on Base before create_all)
from db.base import Base


@pytest.fixture(autouse=True)
def celery_eager_mode():
    """Run Celery tasks synchronously, in-process, against an in-memory result
    backend - no real Redis broker needed for tests or CI."""
    celery_app.conf.update(
        broker_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
    )
    yield


@pytest.fixture()
def db_session_factory():
    """An isolated in-memory SQLite database with the full schema created.

    StaticPool + check_same_thread=False so the single in-memory connection can
    be shared with the worker thread FastAPI's TestClient runs the app in.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    finally:
        engine.dispose()
