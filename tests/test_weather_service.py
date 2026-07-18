import pytest
from fastapi import HTTPException

from app.dto.schemas import CurrentWeatherResponse


async def test_register_user_returns_id(weather_service):
    user_id = await weather_service.register_user("kirill")
    assert isinstance(user_id, int)


async def test_register_user_duplicate_name_raises_409(weather_service):
    await weather_service.register_user("kirill")
    with pytest.raises(HTTPException) as exc_info:
        await weather_service.register_user("kirill")
    assert exc_info.value.status_code == 409


async def test_get_current_weather_by_coords(weather_service):
    result = await weather_service.get_current_weather_by_coords(55.75, 37.61)
    assert isinstance(result, CurrentWeatherResponse)
    assert result.temperature == 18.5
    assert result.wind_speed == 3.4
    assert result.pressure == 1012.1


async def test_get_current_weather_sends_correct_params(weather_service, fake_http_client):
    await weather_service.get_current_weather_by_coords(55.75, 37.61)
    url, params = fake_http_client.calls[-1]
    assert params["latitude"] == 55.75
    assert params["longitude"] == 37.61
    assert "current" in params


async def test_add_city_to_nonexistent_user_raises_404(weather_service):
    with pytest.raises(HTTPException) as exc_info:
        await weather_service.add_city_to_user(999, "Moscow", 55.75, 37.61)
    assert exc_info.value.status_code == 404


async def test_add_city_creates_city_and_links_user(weather_service):
    user_id = await weather_service.register_user("kirill")
    city_id = await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)
    assert isinstance(city_id, int)

    cities = await weather_service.get_user_cities(user_id)
    assert cities == ["Moscow"]


async def test_add_city_fetches_forecast_on_creation(weather_service, fake_http_client):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    hourly_calls = [c for c in fake_http_client.calls if "hourly" in (c[1] or {})]
    assert len(hourly_calls) == 1


async def test_add_existing_city_to_second_user_does_not_refetch(weather_service, fake_http_client):
    user1 = await weather_service.register_user("kirill")
    user2 = await weather_service.register_user("egor")

    await weather_service.add_city_to_user(user1, "Moscow", 55.75, 37.61)
    calls_after_first = len(fake_http_client.calls)

    await weather_service.add_city_to_user(user2, "Moscow", 55.75, 37.61)
    assert len(fake_http_client.calls) == calls_after_first


async def test_add_same_city_twice_to_same_user_is_idempotent(weather_service):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    cities = await weather_service.get_user_cities(user_id)
    assert cities == ["Moscow"]


async def test_get_user_cities_nonexistent_user_raises_404(weather_service):
    with pytest.raises(HTTPException) as exc_info:
        await weather_service.get_user_cities(999)
    assert exc_info.value.status_code == 404


async def test_get_user_cities_empty_list_for_new_user(weather_service):
    user_id = await weather_service.register_user("kirill")
    cities = await weather_service.get_user_cities(user_id)
    assert cities == []


async def test_get_detailed_forecast_city_not_found(weather_service):
    user_id = await weather_service.register_user("kirill")
    with pytest.raises(HTTPException) as exc_info:
        await weather_service.get_detailed_forecast(user_id, "Atlantis", "12:00", None)
    assert exc_info.value.status_code == 404


async def test_get_detailed_forecast_access_denied_for_other_users_city(weather_service):
    owner = await weather_service.register_user("kirill")
    stranger = await weather_service.register_user("egor")
    await weather_service.add_city_to_user(owner, "Moscow", 55.75, 37.61)

    with pytest.raises(HTTPException) as exc_info:
        await weather_service.get_detailed_forecast(stranger, "Moscow", "12:00", None)
    assert exc_info.value.status_code == 403


async def test_get_detailed_forecast_returns_all_params_by_default(weather_service):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    result = await weather_service.get_detailed_forecast(user_id, "Moscow", "12:00", None)
    assert set(result.keys()) == {"temperature", "humidity", "wind_speed", "precipitation"}


async def test_get_detailed_forecast_filters_requested_params(weather_service):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    result = await weather_service.get_detailed_forecast(
        user_id, "Moscow", "12:00", "temperature,humidity"
    )
    assert set(result.keys()) == {"temperature", "humidity"}


async def test_get_detailed_forecast_ignores_invalid_params(weather_service):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    result = await weather_service.get_detailed_forecast(
        user_id, "Moscow", "12:00", "temperature,not_a_real_field"
    )
    assert set(result.keys()) == {"temperature"}


async def test_get_detailed_forecast_no_data_for_time_raises_404(weather_service):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    with pytest.raises(HTTPException) as exc_info:
        await weather_service.get_detailed_forecast(user_id, "Moscow", "12:37", None)
    assert exc_info.value.status_code == 404


async def test_update_all_forecasts_updates_every_city(weather_service, fake_http_client):
    user_id = await weather_service.register_user("kirill")
    await weather_service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)
    await weather_service.add_city_to_user(user_id, "Tomsk", 56.48, 84.95)

    calls_before = len(fake_http_client.calls)
    await weather_service.update_all_forecasts()
    calls_after = len(fake_http_client.calls)

    assert calls_after - calls_before == 2


async def test_update_all_forecasts_continues_after_single_city_error(user_repo, city_repo):
    from tests.conftest import FakeOpenMeteoClient
    from app.services.weather_service import WeatherService

    failing_client = FakeOpenMeteoClient(raise_error=True)
    service = WeatherService(user_repo, city_repo, failing_client)

    user_id = await service.register_user("kirill")
    working_client = failing_client
    working_client.raise_error = False
    await service.add_city_to_user(user_id, "Moscow", 55.75, 37.61)

    working_client.raise_error = True
    await service.update_all_forecasts()
