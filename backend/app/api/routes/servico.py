from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.models.servico import Servico
from app.schemas.servico import (
    ServicoAtualizacao,
    ServicoCriacao,
    ServicoResposta,
)
from app.services.servico import (
    ServicoNaoEncontradoError,
    atualizar_servico,
    cadastrar_servico,
    listar_servicos,
    obter_servico,
)

# Endpoints de gerenciamento de serviços pelo proprietário
# Todos exigem autenticação com token bearer
# O id_estabelecimento vem do token, não da requisição
# Assim um estabelecimento só acessa os próprios serviços
router = APIRouter(prefix="/servicos", tags=["Serviços"])

# Cadastro de serviço
@router.post(
    "",
    response_model=ServicoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_servico(
    dados: ServicoCriacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Servico:
    # Usa o service de cadastro com o id do estabelecimento autenticado
    return cadastrar_servico(
        dados,
        estabelecimento.id_estabelecimento,
        sessao,
    )

# Listagem dos serviços do estabelecimento, ativos e inativos
@router.get("", response_model=list[ServicoResposta])
def consultar_servicos(
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> list[Servico]:
    return listar_servicos(estabelecimento.id_estabelecimento, sessao)

# Consulta de um serviço
@router.get("/{id_servico}", response_model=ServicoResposta)
def consultar_servico(
    id_servico: int,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Servico:
    # Usa o service de consulta
    try:
        servico = obter_servico(
            id_servico,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    # Responde como 404 para serviço inexistente ou de outro estabelecimento
    except ServicoNaoEncontradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    return servico

# Atualização de serviço
# Usa PATCH porque apenas os campos informados são alterados
# Também serve para inativar e reativar o serviço com o campo ativo
@router.patch("/{id_servico}", response_model=ServicoResposta)
def alterar_servico(
    id_servico: int,
    dados: ServicoAtualizacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Servico:
    # Usa o service de atualização
    try:
        servico = atualizar_servico(
            id_servico,
            dados,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    # Responde como 404 para serviço inexistente ou de outro estabelecimento
    except ServicoNaoEncontradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    return servico
