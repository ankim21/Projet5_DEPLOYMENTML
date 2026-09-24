"""Outillage commun aux tests : une base SQLite jetable à la place de PostgreSQL."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_session
from app.main import app
from db.models import Base


def moteur_sqlite(creer_tables: bool = True):
    """Base SQLite en mémoire partagée entre threads (TestClient exécute l'API dans un autre thread)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # une seule connexion -> toutes les sessions voient la même base
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    if creer_tables:
        Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session_factory():
    return sessionmaker(bind=moteur_sqlite(), expire_on_commit=False)


@pytest.fixture
def client(db_session_factory):
    """L'API branchée sur la base de test au lieu de PostgreSQL."""

    def session_de_test():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = session_de_test
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db(db_session_factory):
    """Session pour lire ce que l'API a écrit."""
    with db_session_factory() as session:
        yield session
