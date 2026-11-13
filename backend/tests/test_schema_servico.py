from decimal import Decimal

import pytest
from app.models.servico import Servico
from app.schemas.servico import ServicoAtualizacao, ServicoCriacao, ServicoResposta
from pydantic import ValidationError


def test_schema_servico_criacao():
    # Cria dados válidos para criação do serviço
    dados = {
        "nome": "Corte de cabelo",
        "descricao": "Corte de cabelo",
        "preco": Decimal("35.00"),
        "duracao_minutos": 30,
    }
    # Cria objeto usando o schema
    servico = ServicoCriacao(**dados)
    # Resultado esperado e comparações
    assert servico.nome == "Corte de cabelo"
    assert servico.descricao == "Corte de cabelo"
    assert servico.preco == Decimal("35.00")
    assert servico.duracao_minutos == 30


def test_schema_servico_preco_invalido():
    # Cria dados com preço negativo
    dados = {
        "nome": "Corte de cabelo",
        "preco": Decimal("-10.00"),
        "duracao_minutos": 30,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        ServicoCriacao(**dados)


def test_schema_servico_duracao_invalida():
    # Cria dados com duração zero
    dados = {
        "nome": "Corte de cabelo",
        "preco": Decimal("35.00"),
        "duracao_minutos": 0,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        ServicoCriacao(**dados)


def test_schema_servico_preco_com_casas_decimais_excedentes():
    # Cria dados com três casas decimais
    dados = {
        "nome": "Corte de cabelo",
        "preco": Decimal("35.999"),
        "duracao_minutos": 30,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        ServicoCriacao(**dados)


def test_schema_servico_atualizacao():
    # Cria dados para atualização parcial
    dados = {
        "preco": Decimal("45.00"),
    }
    # Cria objeto com o schema de atualização
    servico = ServicoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    # model_dump transforma o objeto em dicionário, campos não informados ficam como None
    # exclude_unset=True exclui os campos não informados
    assert servico.model_dump(exclude_unset=True) == {
        "preco": Decimal("45.00"),
    }


def test_schema_servico_atualizacao_vazia():
    # Cria dados sem campos para atualização
    dados = {}
    # Tenta criar objeto com o schema de atualização
    with pytest.raises(ValidationError):
        ServicoAtualizacao(**dados)


def test_schema_servico_atualizacao_nome_nulo():
    # Cria dados com nome nulo
    dados = {
        "nome": None,
    }
    # Tenta criar objeto com o schema de atualização
    with pytest.raises(ValidationError):
        ServicoAtualizacao(**dados)


def test_schema_servico_resposta():
    # Cria objeto de serviço
    servico = Servico(
        id_servico=1,
        id_estabelecimento=2,
        nome="Corte de cabelo",
        descricao="Corte tradicional",
        preco=Decimal("35.00"),
        duracao_minutos=30,
        ativo=True,
    )
    # Cria objeto com o schema de resposta usando o objeto de servico
    resposta = ServicoResposta.model_validate(servico)
    # Resultado esperado e comparações
    assert resposta.id_servico == 1
    assert resposta.id_estabelecimento == 2
    assert resposta.nome == "Corte de cabelo"
    assert resposta.descricao == "Corte tradicional"
    assert resposta.preco == Decimal("35.00")
    assert resposta.duracao_minutos == 30
    assert resposta.ativo is True
