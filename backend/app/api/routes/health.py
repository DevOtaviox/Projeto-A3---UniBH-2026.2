from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import obter_sessao_banco

router = APIRouter(tags=["Saúde"])

@router.get("/health")
def verificar_saude():
    return {"status": "ok"}

@router.get("/health/database")
def verificar_banco(
    sessao: Annotated[Session, Depends(obter_sessao_banco)]
):
    sessao.execute(text("SELECT 1"))
    return {"status": "ok"}
