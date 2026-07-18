import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base
from app.api.deps import get_db_session, get_http_client
from app.repo.user_repo import UserSqlliteRepository
from app.repo.city_repo import CitySqlliteRepository
from app.services.weather_service import WeatherService


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest.fixture
def user_repo(db_session):
    return UserSqlliteRepository(db_session)


@pytest.fixture
def city_repo(db_session):
    return CitySqlliteRepository(db_session)


class FakeOpenMeteoClient:
    """Minimal stand-in for httpx.AsyncClient hitting open-meteo."""

    def __init__(self, current_payload=None, hourly_payload=None, raise_error=False):
        self.current_payload = current_payload or {}
        self.hourly_payload = hourly_payload or {}
        self.raise_error = raise_error
        self.calls = []

    async def get(self, url, params=None):
        self.calls.append((url, params))
        if self.raise_error:
            raise httpx.ConnectError("connection failed")
        if params and "current" in params:
            return FakeResponse({"current": self.current_payload})
        return FakeResponse({"hourly": self.hourly_payload})


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json


def make_hourly_payload():
    """24 hourly points for a single day, matching open-meteo's shape."""
    times = [f"2026-07-18T{h:02d}:00" for h in range(24)]
    return {
        "time": times,
        "temperature_2m": [20.0 + i * 0.1 for i in range(24)],
        "relative_humidity_2m": [50 + i for i in range(24)],
        "wind_speed_10m": [3.0 + i * 0.05 for i in range(24)],
        "precipitation": [0.0 for _ in range(24)],
    }


@pytest.fixture
def fake_http_client():
    return FakeOpenMeteoClient(
        current_payload={
            "temperature_2m": 18.5,
            "wind_speed_10m": 3.4,
            "surface_pressure": 1012.1,
        },
        hourly_payload=make_hourly_payload(),
    )


@pytest.fixture
def weather_service(user_repo, city_repo, fake_http_client):
    return WeatherService(user_repo, city_repo, fake_http_client)


@pytest_asyncio.fixture
async def api_client(test_session_factory, fake_http_client):
    async def _override_get_db_session():
        async with test_session_factory() as session:
            yield session

    def _override_get_http_client():
        return fake_http_client

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_http_client] = _override_get_http_client

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
