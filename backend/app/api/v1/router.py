from fastapi import APIRouter
from app.api.v1 import auth, billing, candidates, documents, suppliers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(billing.router)
api_router.include_router(candidates.router)
api_router.include_router(suppliers.router)