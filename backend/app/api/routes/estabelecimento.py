from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoCriacao,
    EstabelecimentoPublicoResposta,
    EstabelecimentoResposta,
)
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    EstabelecimentoNaoEncontradoError,
    buscar_estabelecimento_publico,
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

@router.get(
    "/estabelecimentos/{identificador}",
    response_model=EstabelecimentoPublicoResposta,
)
def consultar_estabelecimento_publico(
    identificador: str,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
):
    # Usa o service de consulta publica
    try:
        estabelecimento = buscar_estabelecimento_publico(identificador, sessao)
    # Responde como 404 para erro de não encontrado retornado pelo service
    except EstabelecimentoNaoEncontradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    return estabelecimento
