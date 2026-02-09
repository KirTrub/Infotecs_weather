from sqlalchemy import select, delete
from typing import List
from app.models.models import City, UserCity, WeatherForecast as Forecast
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod

class ICityRepository(ABC):
    @abstractmethod
    async def get_by_name(self, name: str) -> City | None:
        pass

    @abstractmethod
    async def create(self, name: str, lat: float, lon: float) -> City:
        pass

    @abstractmethod
    async def link_to_user(self, user_id: int, city_id: int) -> None:
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: int) -> List[str]:
        pass

    @abstractmethod
    async def get_all_cities(self) -> List[City]:
        pass

    @abstractmethod
    async def update_forecasts(self, city_id: int, forecasts_data: List[dict]) -> None:
        pass

    @abstractmethod
    async def get_forecast(self, city_id: int, time_str: str) -> Forecast | None:
        pass



class CitySqlliteRepository(ICityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> City | None:
        stmt = select(City).where(City.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, name: str, lat: float, lon: float) -> City:
        city = City(name=name, latitude=lat, longitude=lon)
        self.session.add(city)
        await self.session.commit()
        await self.session.refresh(city)
        return city

    async def link_to_user(self, user_id: int, city_id: int) -> None:
        link = UserCity(user_id=user_id, city_id=city_id)
        self.session.add(link)
        await self.session.commit()

    async def get_all_by_user(self, user_id: int) -> List[str]:
        stmt = select(City.name).join(UserCity).where(UserCity.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_cities(self) -> List[City]:
        stmt = select(City)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_forecasts(self, city_id: int, forecasts_data: List[dict]) -> None:
        await self.session.execute(delete(Forecast).where(Forecast.city_id == city_id))
        
        objects = [Forecast(city_id=city_id, **f) for f in forecasts_data]
        self.session.add_all(objects)
        await self.session.commit()

    async def get_forecast(self, city_id: int, time_str: str) -> Forecast | None:
        from datetime import datetime
        target_time = datetime.strptime(time_str, "%H:%M").time()
        
        stmt = select(Forecast).where(
            Forecast.city_id == city_id, 
            Forecast.time == target_time
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()