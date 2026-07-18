import asyncio
import types

import pytest

import app.main as main_module


class DummyApp:
    def __init__(self, http_client):
        self.state = types.SimpleNamespace(http_client=http_client)


async def test_background_updater_calls_update_and_stops_on_cancel(
    monkeypatch, test_session_factory, fake_http_client
):
    monkeypatch.setattr(main_module, "async_session", test_session_factory)

    call_count = {"n": 0}

    async def fake_sleep(_seconds):
        call_count["n"] += 1
        raise asyncio.CancelledError()

    monkeypatch.setattr(main_module.asyncio, "sleep", fake_sleep)

    dummy_app = DummyApp(fake_http_client)

    async with test_session_factory() as session:
        from app.repo.user_repo import UserSqlliteRepository
        from app.repo.city_repo import CitySqlliteRepository
        from app.services.weather_service import WeatherService

        service = WeatherService(
            UserSqlliteRepository(session), CitySqlliteRepository(session), fake_http_client
        )
        user_id = await service.register_user("kirill")
        await service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    calls_before = len(fake_http_client.calls)


    with pytest.raises(asyncio.CancelledError):
        await main_module.background_weather_updater(dummy_app)

    assert len(fake_http_client.calls) > calls_before
    assert call_count["n"] == 1


async def test_background_updater_survives_exceptions(monkeypatch, test_session_factory):
    monkeypatch.setattr(main_module, "async_session", test_session_factory)

    async def broken_update_all_forecasts(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        main_module.WeatherService, "update_all_forecasts", broken_update_all_forecasts
    )

    reached_sleep = {"flag": False}

    async def fake_sleep(_seconds):
        reached_sleep["flag"] = True
        raise asyncio.CancelledError()

    monkeypatch.setattr(main_module.asyncio, "sleep", fake_sleep)

    dummy_app = DummyApp(http_client=None)

    with pytest.raises(asyncio.CancelledError):
        await main_module.background_weather_updater(dummy_app)

    assert reached_sleep["flag"] is True
