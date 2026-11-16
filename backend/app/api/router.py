from fastapi import APIRouter

from app.api.routes.autenticacao import router as autenticacao_router
from app.api.routes.estabelecimento import router as estabelecimento_router
from app.api.routes.health import router as health_router
from app.api.routes.servico import router as servico_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(estabelecimento_router)
api_router.include_router(autenticacao_router)
api_router.include_router(servico_router)
