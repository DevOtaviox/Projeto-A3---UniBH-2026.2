from fastapi import APIRouter

from app.api.routes.agendamento import router as agendamento_router
from app.api.routes.agendamento import router_publico as agendamento_publico_router
from app.api.routes.autenticacao import router as autenticacao_router
from app.api.routes.estabelecimento import router as estabelecimento_router
from app.api.routes.health import router as health_router
from app.api.routes.horario_funcionamento import router as horario_router
from app.api.routes.horario_funcionamento import router_publico as horario_publico_router
from app.api.routes.servico import router as servico_router
from app.api.routes.servico import router_publico as servico_publico_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(estabelecimento_router)
api_router.include_router(autenticacao_router)
api_router.include_router(servico_router)
api_router.include_router(servico_publico_router)
api_router.include_router(horario_router)
api_router.include_router(horario_publico_router)
api_router.include_router(agendamento_router)
api_router.include_router(agendamento_publico_router)
