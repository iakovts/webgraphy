from fastapi import APIRouter
from .routes import graphs

api_router = APIRouter()
api_router.include_router(graphs.router, prefix="/graphs", tags=["graphs"])