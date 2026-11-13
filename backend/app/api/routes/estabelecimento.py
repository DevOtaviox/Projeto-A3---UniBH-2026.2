from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoCriacao,
    EstabelecimentoResposta,
)
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    cadastrar_estabelecimento,
)

router = APIRouter(tags=["Estabelecimentos"])

# Cadastro de estabelecimento
@router.post(
    "/estabelecimentos",
    response_model=EstabelecimentoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_estabelecimento(
    dados: EstabelecimentoCriacao,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Estabelecimento:
    # Usa o service de cadastro
    try:
        estabelecimento = cadastrar_estabelecimento(dados, sessao)
    # Responde como 409 para erros de duplicidade retornados pelo service
    except EstabelecimentoDuplicadoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        ) from erro
    return estabelecimento
