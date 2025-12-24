from fastapi import APIRouter
from .endpoints import tao_dividends

api_router = APIRouter()

api_router.include_router(
    tao_dividends.router,
    prefix="/tao_dividends",
    tags=["tao_dividends"]
) 