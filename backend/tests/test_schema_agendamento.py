from datetime import date, datetime, time, timedelta

import pytest
from app.models.agendamento import Agendamento
from app.schemas.agendamento import (
    LIMITE_DIAS_AGENDAMENTO,
    AgendamentoAtualizacao,
    AgendamentoCriacao,
    AgendamentoResposta,
)
from pydantic import ValidationError


# Cria dados válidos para criação do agendamento
# As datas são relativas ao dia de hoje pra que os testes não quebrem com o tempo
def dados_validos(**alteracoes):
    dados = {
        "id_servico": 1,
        "nome_cliente": "Maria Silva",
        "telefone_cliente": "31999999999",
        "data_agendamento": date.today() + timedelta(days=1),
        "horario_inicio": time(10, 0),
    }
    # Substitui os campos informados no teste
    dados.update(alteracoes)
    return dados

def test_schema_agendamento_criacao():
    # Cria dados válidos para criação do agendamento
    dados = dados_validos()
    # Cria objeto usando o schema
    agendamento = AgendamentoCriacao(**dados)
    # Resultado esperado e comparações
    assert agendamento.id_servico == 1
    assert agendamento.nome_cliente == "Maria Silva"
    assert agendamento.telefone_cliente == "31999999999"
    assert agendamento.data_agendamento == date.today() + timedelta(days=1)
    assert agendamento.horario_inicio == time(10, 0)

def test_schema_agendamento_telefone_com_mascara():
    # Cria dados com telefone formatado
    dados = dados_validos(telefone_cliente="(31) 99999-9999")
    # Cria objeto usando o schema
    agendamento = AgendamentoCriacao(**dados)
    # Resultado esperado e comparações
    # A máscara é removida e só os números são salvos
    assert agendamento.telefone_cliente == "31999999999"

def test_schema_agendamento_telefone_fixo():
    # Cria dados com telefone fixo (10 dígitos)
    dados = dados_validos(telefone_cliente="3133334444")
    # Cria objeto usando o schema
    agendamento = AgendamentoCriacao(**dados)
    # Resultado esperado e comparações
    assert agendamento.telefone_cliente == "3133334444"

def test_schema_agendamento_telefone_com_letras():
    # Cria dados com telefone contendo letras
    dados = dados_validos(telefone_cliente="3199999999A")
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_telefone_sem_ddd():
    # Cria dados com telefone sem DDD
    dados = dados_validos(telefone_cliente="99999-9999")
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_nome_vazio():
    # Cria dados com nome vazio
    dados = dados_validos(nome_cliente="")
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_servico_invalido():
    # Cria dados com id de serviço zero
    dados = dados_validos(id_servico=0)
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_data_hoje():
    # Cria dados com agendamento para hoje
    dados = dados_validos(data_agendamento=date.today())
    # Cria objeto usando o schema
    agendamento = AgendamentoCriacao(**dados)
    # Resultado esperado e comparações
    assert agendamento.data_agendamento == date.today()

def test_schema_agendamento_data_no_passado():
    # Cria dados com agendamento para ontem
    dados = dados_validos(data_agendamento=date.today() - timedelta(days=1))
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_data_no_limite():
    # Cria dados com agendamento exatamente no último dia permitido
    dados = dados_validos(
        data_agendamento=date.today() + timedelta(days=LIMITE_DIAS_AGENDAMENTO)
    )
    # Cria objeto usando o schema
    agendamento = AgendamentoCriacao(**dados)
    # Resultado esperado e comparações
    assert agendamento.data_agendamento == date.today() + timedelta(
        days=LIMITE_DIAS_AGENDAMENTO
    )

def test_schema_agendamento_data_acima_do_limite():
    # Cria dados com agendamento um dia depois do limite
    dados = dados_validos(
        data_agendamento=date.today() + timedelta(days=LIMITE_DIAS_AGENDAMENTO + 1)
    )
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_horario_fora_do_intervalo():
    # Cria dados com horário que não é múltiplo de 10 minutos
    dados = dados_validos(horario_inicio=time(10, 5))
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_horario_com_segundos():
    # Cria dados com horário contendo segundos
    dados = dados_validos(horario_inicio=time(10, 10, 30))
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        AgendamentoCriacao(**dados)

def test_schema_agendamento_atualizacao_cancelamento():
    # Cria dados para cancelar o agendamento
    dados = {
        "status": "cancelado",
    }
    # Cria objeto com o schema de atualização
    agendamento = AgendamentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    assert agendamento.model_dump(exclude_unset=True) == {
        "status": "cancelado",
    }

def test_schema_agendamento_atualizacao_status_invalido():
    # Cria dados tentando voltar o status para agendado
    dados = {
        "status": "agendado",
    }
    # Tenta criar objeto com o schema de atualização
    with pytest.raises(ValidationError):
        AgendamentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_agendamento_atualizacao_vazia():
    # Cria dados sem campos para atualização
    dados = {}
    # Tenta criar objeto com o schema de atualização
    with pytest.raises(ValidationError):
        AgendamentoAtualizacao(**dados)

def test_schema_agendamento_resposta():
    # Cria objeto de agendamento
    agendamento = Agendamento(
        id_agendamento=1,
        id_servico=2,
        nome_cliente="Maria Silva",
        telefone_cliente="31999999999",
        data_agendamento=date(2026, 11, 20),
        horario_inicio=time(10, 0),
        horario_fim=time(10, 30),
        status="agendado",
        data_cadastro=datetime(2026, 11, 10, 18, 0),
        data_cancelamento=None,
    )
    # Cria objeto com o schema de resposta usando o objeto de agendamento
    resposta = AgendamentoResposta.model_validate(agendamento)
    # Resultado esperado e comparações
    assert resposta.id_agendamento == 1
    assert resposta.id_servico == 2
    assert resposta.nome_cliente == "Maria Silva"
    assert resposta.telefone_cliente == "31999999999"
    assert resposta.data_agendamento == date(2026, 11, 20)
    assert resposta.horario_inicio == time(10, 0)
    assert resposta.horario_fim == time(10, 30)
    assert resposta.status == "agendado"
    assert resposta.data_cadastro == datetime(2026, 11, 10, 18, 0)
    assert resposta.data_cancelamento is None
