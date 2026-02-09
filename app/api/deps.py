from typing import AsyncGenerator
from fastapi import Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.db.session import async_session
from app.repo.user_repo import IUserRepository, UserSqlliteRepository
from app.repo.city_repo import ICityRepository, CitySqlliteRepository
from app.services.weather_service import WeatherService, IWeatherService

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> IUserRepository:
    return UserSqlliteRepository(session)

async def get_city_repository(session: AsyncSession = Depends(get_db_session)) -> ICityRepository:
    return CitySqlliteRepository(session)

def get_weather_service(user_repo: IUserRepository = Depends(get_user_repository), 
                        city_repo: ICityRepository = Depends(get_city_repository),
                        http_client: httpx.AsyncClient = Depends(get_http_client)) -> IWeatherService:
    return WeatherService(user_repo, city_repo, http_client)


