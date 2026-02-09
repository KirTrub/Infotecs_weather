from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from abc import ABC, abstractmethod

from app.repo.user_repo import IUserRepository
from app.repo.city_repo import ICityRepository

from app.dto.schemas import CurrentWeatherResponse


class IWeatherService(ABC):
    @abstractmethod
    async def register_user(self, name: str) -> int:
        pass

    @abstractmethod
    async def get_current_weather_by_coords(self, lat: float, lon: float) -> CurrentWeatherResponse:
        pass

    @abstractmethod
    async def add_city_to_user(self, user_id: int, city_name: str, lat: float, lon: float) -> int:
        pass

    @abstractmethod
    async def get_user_cities(self, user_id: int) -> List[str]:
        pass

    @abstractmethod
    async def get_detailed_forecast(self, user_id: int, city_name: str, time_str: str, params: Optional[str]):
        pass

    @abstractmethod
    async def _fetch_and_save_forecast(self, city_id: int, lat: float, lon: float):
        pass

    @abstractmethod
    async def update_all_forecasts(self):
        pass


class WeatherService(IWeatherService):
    def __init__(self, user_repo: IUserRepository, city_repo: ICityRepository, http_client):
        self.user_repo  =    user_repo
        self.city_repo  =    city_repo
        self.http_client =  http_client 

    async def register_user(self, name: str) -> int:
        try:
            user = await self.user_repo.create(name)
            return user.id
        except Exception:
            raise HTTPException(status_code=409, detail="User already exists")

    async def get_current_weather_by_coords(self, lat: float, lon: float) -> CurrentWeatherResponse:
        response = await self.http_client.get("/forecast", params={
            "latitude": lat,
            "longitude": lon,
            "timezone": "Europe/Moscow",
            "current": "temperature_2m,wind_speed_10m,surface_pressure"
        })
        data = response.json().get("current", {})
        return CurrentWeatherResponse(
            temperature=data.get("temperature_2m"),
            wind_speed=data.get("wind_speed_10m"),
            pressure=data.get("surface_pressure")
        )

    async def add_city_to_user(self, user_id: int, city_name: str, lat: float, lon: float) -> int:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        city = await self.city_repo.get_by_name(city_name)
        if not city:
            city = await self.city_repo.create(city_name, lat, lon)
            await self._fetch_and_save_forecast(city.id, lat, lon)

        is_owned = await self.user_repo.check_ownership(user_id, city.id)
        if not is_owned:
            await self.city_repo.link_to_user(user_id, city.id)
        
        return city.id

    async def get_user_cities(self, user_id: int) -> List[str]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.city_repo.get_all_by_user(user_id)

    async def get_detailed_forecast(self, user_id: int, city_name: str, time_str: str, params: Optional[str]):
        city = await self.city_repo.get_by_name(city_name)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        
        is_owned = await self.user_repo.check_ownership(user_id, city.id)
        if not is_owned:
            raise HTTPException(status_code=403, detail="Access denied to this city")

        forecast = await self.city_repo.get_forecast(city.id, time_str)
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found for this time")

        result = {}
        allowed_params = ["temperature", "humidity", "wind_speed", "precipitation"]
        
        requested_params = [p.strip() for p in params.split(",")] if params else allowed_params
        
        for p in requested_params:
            if p in allowed_params:
                result[p] = getattr(forecast, p)
        
        return result

    async def _fetch_and_save_forecast(self, city_id: int, lat: float, lon: float):
        response = await self.http_client.get("/forecast", params={
            "latitude": lat,
            "longitude": lon,
            "timezone": "Europe/Moscow",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            "forecast_days": 1
        })
        data = response.json().get("hourly", {})
        
        times = data.get("time", [])
        temps = data.get("temperature_2m", [])
        hums = data.get("relative_humidity_2m", [])
        winds = data.get("wind_speed_10m", [])
        precs = data.get("precipitation", [])

        forecasts = []
        for i in range(len(times)):
            dt = datetime.fromisoformat(times[i])
            
            forecasts.append({
                "time": dt.time(),
                "temperature": temps[i],
                "humidity": hums[i],
                "wind_speed": winds[i],
                "precipitation": precs[i]
            })
        
        await self.city_repo.update_forecasts(city_id, forecasts)

    async def update_all_forecasts(self):
        cities = await self.city_repo.get_all_cities()
        for city in cities:
            try:
                await self._fetch_and_save_forecast(city.id, city.latitude, city.longitude)
            except Exception as e:
                print(f"Error updating city {city.name}: {e}")