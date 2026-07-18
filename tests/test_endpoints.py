import pytest


async def test_register_user_endpoint(api_client):
    response = await api_client.post("/users", json={"user_name": "kirill"})
    assert response.status_code == 201
    assert "user_id" in response.json()


async def test_register_duplicate_user_endpoint(api_client):
    await api_client.post("/users", json={"user_name": "kirill"})
    response = await api_client.post("/users", json={"user_name": "kirill"})
    assert response.status_code == 409


async def test_register_user_missing_field_returns_422(api_client):
    response = await api_client.post("/users", json={})
    assert response.status_code == 422


async def test_current_weather_endpoint(api_client):
    response = await api_client.get("/forecast", params={"lat": 55.75, "lon": 37.61})
    assert response.status_code == 200
    body = response.json()
    assert body == {"temperature": 18.5, "wind_speed": 3.4, "pressure": 1012.1}


async def test_current_weather_missing_query_params_returns_422(api_client):
    response = await api_client.get("/forecast")
    assert response.status_code == 422


async def test_add_city_endpoint(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]

    response = await api_client.post(
        f"/users/{user_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )
    assert response.status_code == 200
    assert "city_id" in response.json()


async def test_add_city_to_nonexistent_user_returns_404(api_client):
    response = await api_client.post(
        "/users/999/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )
    assert response.status_code == 404


async def test_get_user_cities_endpoint(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]
    await api_client.post(
        f"/users/{user_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )

    response = await api_client.get(f"/users/{user_id}/cities")
    assert response.status_code == 200
    assert response.json() == ["Moscow"]


async def test_get_cities_for_nonexistent_user_returns_404(api_client):
    response = await api_client.get("/users/999/cities")
    assert response.status_code == 404


async def test_get_detailed_forecast_endpoint(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]
    await api_client.post(
        f"/users/{user_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )

    response = await api_client.get(
        f"/users/{user_id}/cities/Moscow/forecast", params={"time": "12:00"}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"temperature", "humidity", "wind_speed", "precipitation"}


async def test_get_detailed_forecast_with_params_filter(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]
    await api_client.post(
        f"/users/{user_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )

    response = await api_client.get(
        f"/users/{user_id}/cities/Moscow/forecast",
        params={"time": "12:00", "params": "temperature,wind_speed"},
    )
    assert response.status_code == 200
    assert set(response.json().keys()) == {"temperature", "wind_speed"}


async def test_get_detailed_forecast_missing_time_returns_422(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]
    await api_client.post(
        f"/users/{user_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )

    response = await api_client.get(f"/users/{user_id}/cities/Moscow/forecast")
    assert response.status_code == 422


async def test_get_detailed_forecast_unknown_city_returns_404(api_client):
    user_resp = await api_client.post("/users", json={"user_name": "kirill"})
    user_id = user_resp.json()["user_id"]

    response = await api_client.get(
        f"/users/{user_id}/cities/Atlantis/forecast", params={"time": "12:00"}
    )
    assert response.status_code == 404


async def test_get_detailed_forecast_other_users_city_returns_403(api_client):
    owner_resp = await api_client.post("/users", json={"user_name": "kirill"})
    owner_id = owner_resp.json()["user_id"]
    await api_client.post(
        f"/users/{owner_id}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )

    stranger_resp = await api_client.post("/users", json={"user_name": "egor"})
    stranger_id = stranger_resp.json()["user_id"]

    response = await api_client.get(
        f"/users/{stranger_id}/cities/Moscow/forecast", params={"time": "12:00"}
    )
    assert response.status_code == 403


async def test_full_multi_user_flow(api_client):
    kirill = (await api_client.post("/users", json={"user_name": "kirill"})).json()["user_id"]
    egor = (await api_client.post("/users", json={"user_name": "egor"})).json()["user_id"]

    await api_client.post(
        f"/users/{kirill}/cities",
        json={"city_name": "Moscow", "latitude": 55.75, "longitude": 37.61},
    )
    await api_client.post(
        f"/users/{egor}/cities",
        json={"city_name": "Tomsk", "latitude": 56.48, "longitude": 84.95},
    )

    kirill_cities = (await api_client.get(f"/users/{kirill}/cities")).json()
    egor_cities = (await api_client.get(f"/users/{egor}/cities")).json()

    assert kirill_cities == ["Moscow"]
    assert egor_cities == ["Tomsk"]

    forbidden = await api_client.get(
        f"/users/{egor}/cities/Moscow/forecast", params={"time": "12:00"}
    )
    assert forbidden.status_code == 403
