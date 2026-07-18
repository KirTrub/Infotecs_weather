from datetime import time


async def test_user_create_and_get_by_id(user_repo):
    user = await user_repo.create("kirill")
    fetched = await user_repo.get_by_id(user.id)
    assert fetched is not None
    assert fetched.name == "kirill"


async def test_user_get_by_id_missing_returns_none(user_repo):
    fetched = await user_repo.get_by_id(9999)
    assert fetched is None


async def test_check_ownership_false_when_not_linked(user_repo, city_repo):
    user = await user_repo.create("kirill")
    city = await city_repo.create("Moscow", 55.75, 37.61)
    owns = await user_repo.check_ownership(user.id, city.id)
    assert owns is False


async def test_check_ownership_true_when_linked(user_repo, city_repo):
    user = await user_repo.create("kirill")
    city = await city_repo.create("Moscow", 55.75, 37.61)
    await city_repo.link_to_user(user.id, city.id)
    owns = await user_repo.check_ownership(user.id, city.id)
    assert owns is True


async def test_city_create_and_get_by_name(city_repo):
    created = await city_repo.create("Tomsk", 56.48, 84.95)
    fetched = await city_repo.get_by_name("Tomsk")
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.latitude == 56.48


async def test_city_get_by_name_missing_returns_none(city_repo):
    fetched = await city_repo.get_by_name("Atlantis")
    assert fetched is None


async def test_get_all_by_user_returns_only_linked_cities(user_repo, city_repo):
    user = await user_repo.create("kirill")
    moscow = await city_repo.create("Moscow", 55.75, 37.61)
    await city_repo.create("Tomsk", 56.48, 84.95)  # not linked to this user

    await city_repo.link_to_user(user.id, moscow.id)

    cities = await city_repo.get_all_by_user(user.id)
    assert cities == ["Moscow"]


async def test_get_all_cities_returns_every_city(city_repo):
    await city_repo.create("Moscow", 55.75, 37.61)
    await city_repo.create("Tomsk", 56.48, 84.95)

    cities = await city_repo.get_all_cities()
    names = {c.name for c in cities}
    assert names == {"Moscow", "Tomsk"}


async def test_update_forecasts_replaces_old_data(city_repo):
    city = await city_repo.create("Moscow", 55.75, 37.61)

    await city_repo.update_forecasts(city.id, [
        {"time": time(12, 0), "temperature": 10.0, "humidity": 50, "wind_speed": 3.0, "precipitation": 0.0}
    ])
    first = await city_repo.get_forecast(city.id, "12:00")
    assert first.temperature == 10.0

    # second update should replace, not append, the old forecast rows
    await city_repo.update_forecasts(city.id, [
        {"time": time(12, 0), "temperature": 20.0, "humidity": 60, "wind_speed": 4.0, "precipitation": 1.0}
    ])
    second = await city_repo.get_forecast(city.id, "12:00")
    assert second.temperature == 20.0


async def test_get_forecast_missing_time_returns_none(city_repo):
    city = await city_repo.create("Moscow", 55.75, 37.61)
    await city_repo.update_forecasts(city.id, [
        {"time": time(12, 0), "temperature": 10.0, "humidity": 50, "wind_speed": 3.0, "precipitation": 0.0}
    ])
    forecast = await city_repo.get_forecast(city.id, "18:00")
    assert forecast is None
