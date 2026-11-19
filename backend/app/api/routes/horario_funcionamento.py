from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.models.horario_funcionamento import HorarioFuncionamento
from app.schemas.horario_funcionamento import (
    HorarioFuncionamentoAtualizacao,
    HorarioFuncionamentoCriacao,
    HorarioFuncionamentoResposta,
)
from app.services.estabelecimento import EstabelecimentoNaoEncontradoError
from app.services.horario_funcionamento import (
    HorarioInvalidoError,
    HorarioNaoConfiguradoError,
    atualizar_horario,
    definir_horario,
    obter_horario,
    obter_horario_publico,
)

# Endpoints do horário de funcionamento do proprietário
# Todos exigem autenticação com token bearer
# O id_estabelecimento vem do token, não da requisição
router = APIRouter(
    prefix="/horario-funcionamento",
    tags=["Horário de funcionamento"],
)

# Endpoint público usado pelo cliente na página do estabelecimento
# Não exige autenticação
router_publico = APIRouter(tags=["Horário de funcionamento"])

# Consulta do horário de funcionamento
@router.get("", response_model=HorarioFuncionamentoResposta)
def consultar_horario(
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> HorarioFuncionamento:
    # Responde como 404 se o horário ainda não foi configurado
    try:
        return obter_horario(estabelecimento.id_estabelecimento, sessao)
    except HorarioNaoConfiguradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro

# Cria ou substitui o horário de funcionamento
# Usa PUT porque o horário inteiro é enviado e cada estabelecimento tem só um
@router.put("", response_model=HorarioFuncionamentoResposta)
def configurar_horario(
    dados: HorarioFuncionamentoCriacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> HorarioFuncionamento:
    return definir_horario(dados, estabelecimento.id_estabelecimento, sessao)

# Atualização parcial do horário de funcionamento
@router.patch("", response_model=HorarioFuncionamentoResposta)
def alterar_horario(
    dados: HorarioFuncionamentoAtualizacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> HorarioFuncionamento:
    try:
        return atualizar_horario(
            dados,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    # Responde como 404 se o horário ainda não foi configurado
    except HorarioNaoConfiguradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    # Responde como 422 se o horário resultante for inválido
    except HorarioInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro

# Consulta pública do horário de funcionamento pelo identificador
@router_publico.get(
    "/estabelecimentos/{identificador}/horario-funcionamento",
    response_model=HorarioFuncionamentoResposta,
)
def consultar_horario_publico(
    identificador: str,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> HorarioFuncionamento:
    # Responde como 404 se o estabelecimento não existir, estiver inativo
    # ou ainda não tiver configurado o horário
    try:
        return obter_horario_publico(identificador, sessao)
    except (
        EstabelecimentoNaoEncontradoError,
        HorarioNaoConfiguradoError,
    ) as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
