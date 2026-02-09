from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.dto.schemas import (
    UserCreate, UserResponse, 
    CityCreate, CityResponse, 
    CurrentWeatherResponse
)
from app.services.weather_service import IWeatherService
from app.api.deps import get_weather_service

routes = APIRouter()

@routes.post("/users", response_model=UserResponse, status_code=201)
async def register_user(
    req: UserCreate,
    service: IWeatherService = Depends(get_weather_service)
):
    user_id = await service.register_user(req.user_name)
    return UserResponse(user_id=user_id)

@routes.post("/users/{user_id}/cities", response_model=CityResponse)
async def add_city(
    user_id: int,
    req: CityCreate,
    service: IWeatherService = Depends(get_weather_service)
):
    city_id = await service.add_city_to_user(user_id, req.city_name, req.latitude, req.longitude)
    return CityResponse(city_id=city_id)

@routes.get("/users/{user_id}/cities", response_model=List[str])
async def get_cities(
    user_id: int,
    service: IWeatherService = Depends(get_weather_service)
):
    return await service.get_user_cities(user_id)

@routes.get("/users/{user_id}/cities/{city_name}/forecast")
async def get_forecast(
    user_id: int,
    city_name: str,
    time: str = Query(..., description="Format HH:MM"),
    params: Optional[str] = Query(None),
    service: IWeatherService = Depends(get_weather_service)
):
    return await service.get_detailed_forecast(user_id, city_name, time, params)

@routes.get("/forecast", response_model=CurrentWeatherResponse)
async def get_current_weather(
    lat: float, 
    lon: float,
    service: IWeatherService = Depends(get_weather_service)
):
    return await service.get_current_weather_by_coords(lat, lon)