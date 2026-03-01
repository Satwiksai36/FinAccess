from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.predict import router as predict_router
from app.api.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router, tags=["system"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(predict_router, prefix="/predict", tags=["predict"])
