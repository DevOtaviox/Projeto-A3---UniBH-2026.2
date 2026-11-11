from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.api.router import api_router
from app.db.base import BaseModelos
from app.db.session import motor_banco


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas se não existirem no banco usando a engine do SQLAlchemy
    BaseModelos.metadata.create_all(bind=motor_banco)
    yield

app = FastAPI(
    title="API Plataforma de Agendamentos",
    description="API para gerenciamento de agendamentos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)
