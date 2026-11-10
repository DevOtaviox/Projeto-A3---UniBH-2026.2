from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="API Plataforma de Agendamentos",
    description="API para gerenciamento de agendamentos.",
    version="1.0.0",
)

app.include_router(api_router)
