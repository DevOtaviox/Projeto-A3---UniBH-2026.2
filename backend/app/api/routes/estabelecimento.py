from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoAtualizacao,
    EstabelecimentoCriacao,
    EstabelecimentoPublicoResposta,
    EstabelecimentoResposta,
)
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    EstabelecimentoNaoEncontradoError,
    atualizar_estabelecimento,
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

# Consulta dos dados do estabelecimento autenticado
# Precisa ficar antes de /estabelecimentos/{identificador}
# Senão o FastAPI trataria "me" como um identificador
@router.get(
    "/estabelecimentos/me",
    response_model=EstabelecimentoResposta,
)
def consultar_meu_estabelecimento(
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
) -> Estabelecimento:
    return estabelecimento

# Atualização do estabelecimento autenticado
# Usa PATCH porque apenas os campos informados são alterados
# O id vem do token, então um estabelecimento só altera os próprios dados
@router.patch(
    "/estabelecimentos/me",
    response_model=EstabelecimentoResposta,
)
def alterar_meu_estabelecimento(
    dados: EstabelecimentoAtualizacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Estabelecimento:
    # Usa o service de atualização
    try:
        estabelecimento = atualizar_estabelecimento(
            estabelecimento,
            dados,
            sessao,
        )
    # Responde como 409 para erros de duplicidade retornados pelo service
    except EstabelecimentoDuplicadoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        ) from erro
    return estabelecimento

# Consulta pública do estabelecimento pelo identificador
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
