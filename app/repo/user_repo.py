from sqlalchemy import select
from app.models.models import User, UserCity
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    async def create(self, name: str) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def check_ownership(self, user_id: int, city_id: int) -> bool:
        pass
        



class UserSqlliteRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, name: str) -> User:
        user = User(name=name)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def check_ownership(self, user_id: int, city_id: int) -> bool:
        stmt = select(UserCity).where(
            UserCity.user_id == user_id, 
            UserCity.city_id == city_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None