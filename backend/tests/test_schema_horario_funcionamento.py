from datetime import time

import pytest
from app.models.horario_funcionamento import HorarioFuncionamento
from app.schemas.horario_funcionamento import (
    HorarioFuncionamentoAtualizacao,
    HorarioFuncionamentoCriacao,
    HorarioFuncionamentoResposta,
)
from pydantic import ValidationError


def test_schema_horario_funcionamento_criacao():
    # Cria dados válidos para criação do horário
    dados = {
        "segunda": True,
        "terca": True,
        "quarta": True,
        "quinta": True,
        "sexta": True,
        "sabado": True,
        "domingo": False,
        "hora_abertura": time(8, 0),
        "hora_fechamento": time(18, 0),
        "inicio_intervalo": time(12, 0),
        "fim_intervalo": time(13, 0),
    }
    # Cria objeto usando o schema
    horario = HorarioFuncionamentoCriacao(**dados)
    # Resultado esperado e comparações
    assert horario.segunda is True
    assert horario.terca is True
    assert horario.quarta is True
    assert horario.quinta is True
    assert horario.sexta is True
    assert horario.sabado is True
    assert horario.domingo is False
    assert horario.hora_abertura == time(8, 0)
    assert horario.hora_fechamento == time(18, 0)
    assert horario.inicio_intervalo == time(12, 0)
    assert horario.fim_intervalo == time(13, 0)

def test_schema_horario_funcionamento_sem_dias():
    # Cria dados sem dias de funcionamento
    dados = {
        "hora_abertura": time(8, 0),
        "hora_fechamento": time(18, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_horario_funcionamento_horarios_invalidos():
    # Cria dados com abertura igual ao fechamento
    dados = {
        "segunda": True,
        "hora_abertura": time(18, 0),
        "hora_fechamento": time(18, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoCriacao(**dados)

def test_schema_horario_funcionamento_intervalo_incompleto():
    # Cria dados com apenas o início do intervalo
    dados = {
        "segunda": True,
        "hora_abertura": time(8, 0),
        "hora_fechamento": time(18, 0),
        "inicio_intervalo": time(12, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoCriacao(**dados)

def test_schema_horario_funcionamento_intervalo_fora_do_horario():
    # Cria dados com intervalo fora do funcionamento
    dados = {
        "segunda": True,
        "hora_abertura": time(8, 0),
        "hora_fechamento": time(18, 0),
        "inicio_intervalo": time(7, 0),
        "fim_intervalo": time(8, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoCriacao(**dados)

def test_schema_horario_funcionamento_intervalo_ordem_invalida():
    # Cria dados com início do intervalo depois do fim
    dados = {
        "segunda": True,
        "hora_abertura": time(8, 0),
        "hora_fechamento": time(18, 0),
        "inicio_intervalo": time(13, 0),
        "fim_intervalo": time(12, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoCriacao(**dados)

def test_schema_horario_funcionamento_atualizacao():
    # Cria dados para atualização parcial
    dados = {
        "sabado": True,
    }
    # Cria objeto com o schema de atualização
    horario = HorarioFuncionamentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    # model_dump transforma o objeto em dicionário, campos não informados ficam como None
    # exclude_unset=True exclui os campos não informados
    assert horario.model_dump(exclude_unset=True) == {
        "sabado": True,
    }

def test_schema_horario_funcionamento_atualizacao_vazia():
    # Cria dados sem campos para atualização
    dados = {}
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoAtualizacao(**dados)

def test_schema_horario_funcionamento_atualizacao_dia_nulo():
    # Cria dados com dia de funcionamento nulo
    dados = {
        "segunda": None,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoAtualizacao(**dados)

def test_schema_horario_funcionamento_atualizacao_intervalo_incompleto():
    # Cria dados para remover apenas o início do intervalo
    dados = {
        "inicio_intervalo": None,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoAtualizacao(**dados)

def test_schema_horario_funcionamento_atualizacao_remover_intervalo():
    # Cria dados para remover o intervalo
    dados = {
        "inicio_intervalo": None,
        "fim_intervalo": None,
    }
    # Cria objeto com o schema de atualização
    horario = HorarioFuncionamentoAtualizacao(**dados)
    # Resultado esperado e comparações
    assert horario.model_dump(exclude_unset=True) == {
        "inicio_intervalo": None,
        "fim_intervalo": None,
    }

def test_schema_horario_funcionamento_atualizacao_intervalo_ordem_invalida():
    # Cria dados com início do intervalo posterior ao fim
    dados = {
        "inicio_intervalo": time(13, 0),
        "fim_intervalo": time(12, 0),
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        HorarioFuncionamentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_horario_funcionamento_resposta():
    # Cria objeto de horário de funcionamento
    horario = HorarioFuncionamento(
        id_horario=1,
        id_estabelecimento=2,
        segunda=True,
        terca=True,
        quarta=True,
        quinta=True,
        sexta=True,
        sabado=True,
        domingo=False,
        hora_abertura=time(8, 0),
        hora_fechamento=time(18, 0),
        inicio_intervalo=time(12, 0),
        fim_intervalo=time(13, 0),
    )
    # Cria objeto com o schema de resposta usando o objeto de horario
    resposta = HorarioFuncionamentoResposta.model_validate(horario)
    # Resultado esperado e comparações
    assert resposta.id_horario == 1
    assert resposta.id_estabelecimento == 2
    assert resposta.segunda is True
    assert resposta.terca is True
    assert resposta.quarta is True
    assert resposta.quinta is True
    assert resposta.sexta is True
    assert resposta.sabado is True
    assert resposta.domingo is False
    assert resposta.hora_abertura == time(8, 0)
    assert resposta.hora_fechamento == time(18, 0)
    assert resposta.inicio_intervalo == time(12, 0)
    assert resposta.fim_intervalo == time(13, 0)
