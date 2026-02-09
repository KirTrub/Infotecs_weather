from sqlalchemy import ForeignKey, Time
from datetime import time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    cities = relationship("City", secondary="user_cities", back_populates="users")

class City(Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    users = relationship("User", secondary="user_cities", back_populates="cities")

class UserCity(Base):
    __tablename__ = "user_cities"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), primary_key=True)

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"
    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    time: Mapped[time] = mapped_column(Time) 
    temperature: Mapped[float] = mapped_column()
    humidity: Mapped[float] = mapped_column()
    wind_speed: Mapped[float] = mapped_column()
    precipitation: Mapped[float] = mapped_column()