from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def pytest_addoption(parser):
    parser.addoption(
        "--live-r",
        action="store_true",
        default=False,
        help="Run tests against a live R Plumber service (localhost:8787)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live_r: requires live R Plumber service")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live-r"):
        return
    skip_live = pytest.mark.skip(reason="needs --live-r option to run")
    for item in items:
        if "live_r" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session", autouse=True)
def test_settings(tmp_path_factory):
    from app.core.config import Settings
    import app.core.config as config

    tmp_root = tmp_path_factory.mktemp("test_data")
    settings = Settings(
        DEBUG=True,
        JWT_SECRET_KEY="test-secret",
        DATABASE_URL="sqlite:///:memory:",
        UPLOAD_ROOT=tmp_root / "uploads",
        ARTIFACT_ROOT=tmp_root / "artifacts",
    )
    config._settings = settings
    return settings


@pytest.fixture
def engine(test_settings):
    from app.db.base import Base
    import app.models  # noqa: F401

    eng = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest.fixture
def db_session(session_factory) -> Session:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def app(test_settings, session_factory):
    from app.core.config import get_settings
    from app.db.session import get_db
    from app.main import create_app

    fastapi_app = create_app()

    def override_get_settings():
        return test_settings

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_settings] = override_get_settings
    fastapi_app.dependency_overrides[get_db] = override_get_db
    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client


@pytest.fixture
def create_test_user(db_session):
    from app.repositories.users import UserRepository
    from app.services.auth_service import AuthService

    def _create(
        username: str = "testuser",
        password: str = "testpass123",
        display_name: str | None = None,
        is_active: bool = True,
    ):
        svc = AuthService(db_session)
        auth_session = svc.register(
            username=username,
            password=password,
            display_name=display_name,
        )
        user = UserRepository(db_session).get_by_username(username)
        if user and not is_active:
            user.is_active = False
            db_session.commit()
        return user, password, auth_session

    return _create


@pytest.fixture
def auth_headers(create_test_user) -> dict[str, str]:
    _user, _password, session = create_test_user()
    return {"Authorization": f"Bearer {session.access_token}"}


# ---------------------------------------------------------------------------
# E2E integration fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def eager_celery(session_factory):
    """Enable Celery eager mode and patch SessionLocal for inline task execution.

    In eager mode, `task.delay()` runs synchronously. We also patch
    ``SessionLocal`` in the tasks module so the Celery task uses the same
    in-memory test database (via StaticPool) as the API handler.
    """
    from app.workers.celery_worker import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    with patch("app.tasks.analysis_tasks.SessionLocal", session_factory):
        yield

    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False


def _make_test_dataframe(n_per_group: int = 20, seed: int = 42) -> pd.DataFrame:
    """Synthetic data with 3 groups and 2 numeric columns."""
    import numpy as np

    rng = np.random.default_rng(seed)
    groups = ["A"] * n_per_group + ["B"] * n_per_group + ["C"] * n_per_group
    v1 = (
        rng.normal(10, 2, n_per_group).tolist()
        + rng.normal(15, 3, n_per_group).tolist()
        + rng.normal(12, 1.8, n_per_group).tolist()
    )
    v2 = (
        rng.normal(5, 1, n_per_group).tolist()
        + rng.normal(8, 1.5, n_per_group).tolist()
        + rng.normal(6, 1.2, n_per_group).tolist()
    )
    return pd.DataFrame(
        {
            "group": groups,
            "value1": [round(x, 4) for x in v1],
            "value2": [round(x, 4) for x in v2],
        }
    )


@pytest.fixture
def test_dataset(db_session, test_settings, create_test_user):
    """Create a user, dataset and revision with a real CSV on disk.

    Returns a dict with ``user``, ``auth_headers``, ``dataset_id``,
    ``revision_id`` and ``csv_path``.
    """
    from app.models.dataset import Dataset
    from app.models.dataset_revision import DatasetRevision

    user, _pw, auth_session = create_test_user()
    headers = {"Authorization": f"Bearer {auth_session.access_token}"}

    df = _make_test_dataframe()

    dataset = Dataset(
        owner_id=user.id,
        name="test_data",
        original_filename="test_data.csv",
        file_type="csv",
    )
    db_session.add(dataset)
    db_session.flush()

    storage_dir = Path(str(test_settings.UPLOAD_ROOT)) / user.id / dataset.id
    storage_dir.mkdir(parents=True, exist_ok=True)
    csv_path = storage_dir / "v1.csv"
    df.to_csv(csv_path, index=False)

    revision = DatasetRevision(
        dataset_id=dataset.id,
        version=1,
        storage_path=str(csv_path),
        row_count=len(df),
        col_count=len(df.columns),
        source_type="upload",
    )
    db_session.add(revision)
    db_session.commit()

    return {
        "user": user,
        "auth_headers": headers,
        "dataset_id": dataset.id,
        "revision_id": revision.id,
        "csv_path": str(csv_path),
    }
