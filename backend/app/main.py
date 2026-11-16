
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.api.router import api_router
from app.db.base import BaseModelos
from app.db.session import motor_banco


@asynccontextmanager
async def lifespan(app: FastAPI):
    # cria as tabelas se nao existirem no banco
    BaseModelos.metadata.create_all(bind=motor_banco)
    yield


app = FastAPI(
    title="API Plataforma de Agendamentos",
    description="API para gerenciamento de agendamentos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
