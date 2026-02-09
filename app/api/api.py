from fastapi import APIRouter
from app.api.endpoints.endpoints import routes

router = APIRouter()

router.include_router(routes)

            



