from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.agendamento import Agendamento
from app.models.estabelecimento import Estabelecimento
from app.schemas.agendamento import (
    AgendamentoAtualizacao,
    AgendamentoCriacao,
    AgendamentoResposta,
    DisponibilidadeResposta,
)
from app.services.agendamento import (
    AgendamentoCanceladoError,
    AgendamentoInvalidoError,
    AgendamentoNaoEncontradoError,
    HorarioIndisponivelError,
    cadastrar_agendamento,
    cadastrar_agendamento_publico,
    cancelar_agendamento,
    consultar_disponibilidade,
    listar_agendamentos,
    obter_agendamento,
)
from app.services.estabelecimento import EstabelecimentoNaoEncontradoError
from app.services.servico import ServicoNaoEncontradoError

# Endpoints de gerenciamento de agendamentos pelo proprietário
# Todos exigem autenticação com token bearer
# O id_estabelecimento vem do token, não da requisição
router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])

# Endpoints públicos usados pelo cliente na página do estabelecimento
# Não exigem autenticação
router_publico = APIRouter(tags=["Agendamentos"])

# Código HTTP de cada erro retornado pelos services
# 404: recurso não encontrado
# 409: conflito com o estado atual (horário ocupado, já cancelado)
# 422: horário que não respeita as regras do estabelecimento
CODIGOS_ERRO = {
    EstabelecimentoNaoEncontradoError: status.HTTP_404_NOT_FOUND,
    ServicoNaoEncontradoError: status.HTTP_404_NOT_FOUND,
    AgendamentoNaoEncontradoError: status.HTTP_404_NOT_FOUND,
    HorarioIndisponivelError: status.HTTP_409_CONFLICT,
    AgendamentoCanceladoError: status.HTTP_409_CONFLICT,
    AgendamentoInvalidoError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}
ERROS_TRATADOS = tuple(CODIGOS_ERRO)

# Converte um erro do service na resposta HTTP correspondente
def converter_erro(erro: Exception) -> HTTPException:
    return HTTPException(
        status_code=CODIGOS_ERRO[type(erro)],
        detail=str(erro),
    )

# Cadastro de agendamento pelo proprietário (ex.: cliente ligou ou veio ao local)
@router.post(
    "",
    response_model=AgendamentoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento(
    dados: AgendamentoCriacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Agendamento:
    try:
        return cadastrar_agendamento(
            dados,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    except ERROS_TRATADOS as erro:
        raise converter_erro(erro) from erro

# Listagem dos agendamentos do estabelecimento
# Filtros opcionais: ?data=AAAA-MM-DD e ?status=agendado|cancelado
@router.get("", response_model=list[AgendamentoResposta])
def consultar_agendamentos(
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
    data: date | None = None,
    status_agendamento: Annotated[
        Literal["agendado", "cancelado"] | None,
        Query(alias="status"),
    ] = None,
) -> list[Agendamento]:
    return listar_agendamentos(
        estabelecimento.id_estabelecimento,
        sessao,
        data_agendamento=data,
        status=status_agendamento,
    )

# Consulta de um agendamento
@router.get("/{id_agendamento}", response_model=AgendamentoResposta)
def consultar_agendamento(
    id_agendamento: int,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Agendamento:
    try:
        return obter_agendamento(
            id_agendamento,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    except ERROS_TRATADOS as erro:
        raise converter_erro(erro) from erro

# Cancelamento de agendamento (RF20 e RF21)
# Pelo schema, a única alteração permitida é {"status": "cancelado"}
# O agendamento não é excluído e o horário volta a ficar disponível
@router.patch("/{id_agendamento}", response_model=AgendamentoResposta)
def alterar_agendamento(
    id_agendamento: int,
    dados: AgendamentoAtualizacao,  # noqa: ARG001
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Agendamento:
    # dados.status sempre é "cancelado", o schema não aceita outro valor
    try:
        return cancelar_agendamento(
            id_agendamento,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    except ERROS_TRATADOS as erro:
        raise converter_erro(erro) from erro

# Consulta pública dos horários disponíveis de um serviço em uma data
# Ex.: /estabelecimentos/barbearia-joao/disponibilidade?id_servico=1&data=2026-11-20
@router_publico.get(
    "/estabelecimentos/{identificador}/disponibilidade",
    response_model=DisponibilidadeResposta,
)
def consultar_horarios_disponiveis(
    identificador: str,
    id_servico: Annotated[int, Query(gt=0)],
    data: date,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> DisponibilidadeResposta:
    try:
        servico, horarios = consultar_disponibilidade(
            identificador,
            id_servico,
            data,
            sessao,
        )
    except ERROS_TRATADOS as erro:
        raise converter_erro(erro) from erro
    return DisponibilidadeResposta(
        id_servico=servico.id_servico,
        data_agendamento=data,
        duracao_minutos=servico.duracao_minutos,
        horarios=horarios,
    )

# Cadastro de agendamento pelo cliente na página pública
# O sistema confere se o horário continua livre antes de salvar
@router_publico.post(
    "/estabelecimentos/{identificador}/agendamentos",
    response_model=AgendamentoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento_publico(
    identificador: str,
    dados: AgendamentoCriacao,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Agendamento:
    try:
        return cadastrar_agendamento_publico(identificador, dados, sessao)
    except ERROS_TRATADOS as erro:
        raise converter_erro(erro) from erro
