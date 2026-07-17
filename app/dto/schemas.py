from pydantic import BaseModel, Field
from typing import Optional

class UserCreateRequest(BaseModel):
    user_name: str = Field(min_length=5, max_length=100)

class UserCreateResponse(BaseModel):
    user_id: int

class CityCreateRequest(BaseModel):
    city_name: str = Field(min_length=2, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le = 180)

class CityCreateResponse(BaseModel):
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
