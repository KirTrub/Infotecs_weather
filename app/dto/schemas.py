from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    user_name: str

class UserResponse(BaseModel):
    user_id: int

class CityCreate(BaseModel):
    city_name: str
    latitude: float
    longitude: float

class CityResponse(BaseModel):
    city_id: int
    status: str = "OK"

class ForecastResponse(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None

class CurrentWeatherResponse(BaseModel):
    temperature: float
    wind_speed: float
    pressure: float