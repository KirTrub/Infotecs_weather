import asyncio
from contextlib import asynccontextmanager
import contextlib
from fastapi import FastAPI
import httpx

from app.api.api import router
from app.db.session import engine, Base, async_session

from app.repo.user_repo import UserSqlliteRepository
from app.repo.city_repo import CitySqlliteRepository

from app.services.weather_service import WeatherService

async def background_weather_updater(app):
    while True:
        try:
            async with async_session() as session:
                user_repo = UserSqlliteRepository(session)
                city_repo = CitySqlliteRepository(session)
                service = WeatherService(user_repo, city_repo, app.state.http_client)
                
                await service.update_all_forecasts()
                print("Forecasts updated")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in background update: {e}")
        
        await asyncio.sleep(15 * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.http_client = httpx.AsyncClient(
        base_url="https://api.open-meteo.com/v1",
        timeout=5.0,
    )

    updater_task = asyncio.create_task(background_weather_updater(app))

    try:
        yield
    finally:
        updater_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await updater_task

        await app.state.http_client.aclose()
        await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(router)