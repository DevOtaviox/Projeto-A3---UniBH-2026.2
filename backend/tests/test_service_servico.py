from decimal import Decimal

import pytest
from app.models.estabelecimento import Estabelecimento
from app.models.servico import Servico
from app.schemas.servico import ServicoAtualizacao, ServicoCriacao
from app.services.servico import (
    ServicoNaoEncontradoError,
    atualizar_servico,
    cadastrar_servico,
    listar_servicos,
    obter_servico,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


# Cria estabelecimento de teste
def criar_estabelecimento(
    sessao_teste,
    email="joao@example.com",
    documento="12345678901",
    identificador="barbearia-joao",
):
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento=documento,
        identificador=identificador,
        email=email,
        senha_hash="hash-teste",
    )
    # Adiciona e salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

# Cria um segundo estabelecimento pra testar o isolamento dos serviços
def criar_outro_estabelecimento(sessao_teste):
    return criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )

# Cria dados para cadastro
def criar_dados_servico(nome="Corte de cabelo"):
    return ServicoCriacao(
        nome=nome,
        descricao="Corte tradicional",
        preco=Decimal("35.00"),
        duracao_minutos=30,
    )

def test_cadastrar_servico(sessao_teste):
    # Cria estabelecimento e dados para cadastro
    estabelecimento = criar_estabelecimento(sessao_teste)
    dados = criar_dados_servico()
    # Cadastra o serviço usando o Service
    servico = cadastrar_servico(
        dados,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria um gerador de sessões para consulta
    gerador_sessoes = sessionmaker(bind=sessao_teste.get_bind())
    with gerador_sessoes() as sessao_consulta:
        servico_salvo = sessao_consulta.get(Servico, servico.id_servico)
    # Resultado esperado e comparações
    assert servico_salvo is not None
    assert servico_salvo.id_estabelecimento == estabelecimento.id_estabelecimento
    assert servico_salvo.nome == "Corte de cabelo"
    assert servico_salvo.descricao == "Corte tradicional"
    assert servico_salvo.preco == Decimal("35.00")
    assert servico_salvo.duracao_minutos == 30
    assert servico_salvo.ativo is True

def test_cadastrar_servico_estabelecimento_inexistente(sessao_teste):
    # Cria dados para cadastro
    dados = criar_dados_servico()
    # Tenta cadastrar serviço para um estabelecimento que não existe
    with pytest.raises(IntegrityError):
        cadastrar_servico(dados, 999, sessao_teste)

def test_listar_servicos(sessao_teste):
    # Cria estabelecimento e cadastra dois serviços
    estabelecimento = criar_estabelecimento(sessao_teste)
    cadastrar_servico(
        criar_dados_servico("Corte de cabelo"),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    cadastrar_servico(
        criar_dados_servico("Barba"),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Lista os serviços do estabelecimento
    servicos = listar_servicos(
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert [servico.nome for servico in servicos] == [
        "Corte de cabelo",
        "Barba",
    ]

def test_listar_servicos_sem_cadastro(sessao_teste):
    # Cria estabelecimento sem serviços
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Lista os serviços do estabelecimento
    servicos = listar_servicos(
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert servicos == []

def test_listar_servicos_apenas_do_estabelecimento(sessao_teste):
    # Cria dois estabelecimentos com um serviço cada
    estabelecimento = criar_estabelecimento(sessao_teste)
    outro_estabelecimento = criar_outro_estabelecimento(sessao_teste)
    cadastrar_servico(
        criar_dados_servico("Corte de cabelo"),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    cadastrar_servico(
        criar_dados_servico("Manicure"),
        outro_estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Lista os serviços do primeiro estabelecimento
    servicos = listar_servicos(
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    # O serviço do outro estabelecimento não pode aparecer
    assert [servico.nome for servico in servicos] == ["Corte de cabelo"]

def test_obter_servico(sessao_teste):
    # Cria estabelecimento e cadastra serviço
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Consulta o serviço
    resultado = obter_servico(
        servico.id_servico,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert resultado.id_servico == servico.id_servico
    assert resultado.nome == "Corte de cabelo"

def test_obter_servico_inexistente(sessao_teste):
    # Cria estabelecimento sem serviços
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Tenta consultar serviço inexistente
    with pytest.raises(ServicoNaoEncontradoError):
        obter_servico(999, estabelecimento.id_estabelecimento, sessao_teste)

def test_obter_servico_de_outro_estabelecimento(sessao_teste):
    # Cria dois estabelecimentos e um serviço para o primeiro
    estabelecimento = criar_estabelecimento(sessao_teste)
    outro_estabelecimento = criar_outro_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Tenta consultar o serviço usando o id do outro estabelecimento
    with pytest.raises(ServicoNaoEncontradoError):
        obter_servico(
            servico.id_servico,
            outro_estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_servico(sessao_teste):
    # Cria estabelecimento e cadastra serviço
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria dados para atualização parcial
    dados = ServicoAtualizacao(preco=Decimal("45.00"))  # pyright: ignore[reportCallIssue]
    # Atualiza o serviço usando o Service
    atualizar_servico(
        servico.id_servico,
        dados,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria um gerador de sessões para consulta
    gerador_sessoes = sessionmaker(bind=sessao_teste.get_bind())
    with gerador_sessoes() as sessao_consulta:
        servico_salvo = sessao_consulta.get(Servico, servico.id_servico)
    # Resultado esperado e comparações
    # Apenas o preço é alterado, os outros campos permanecem iguais
    assert servico_salvo is not None
    assert servico_salvo.preco == Decimal("45.00")
    assert servico_salvo.nome == "Corte de cabelo"
    assert servico_salvo.descricao == "Corte tradicional"
    assert servico_salvo.duracao_minutos == 30
    assert servico_salvo.ativo is True

def test_atualizar_servico_inativar(sessao_teste):
    # Cria estabelecimento e cadastra serviço
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria dados para inativar o serviço
    dados = ServicoAtualizacao(ativo=False)  # pyright: ignore[reportCallIssue]
    # Atualiza o serviço usando o Service
    resultado = atualizar_servico(
        servico.id_servico,
        dados,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    # O serviço continua existindo no db, apenas inativo
    assert resultado.ativo is False
    assert len(
        listar_servicos(estabelecimento.id_estabelecimento, sessao_teste)
    ) == 1

def test_atualizar_servico_remover_descricao(sessao_teste):
    # Cria estabelecimento e cadastra serviço
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria dados para remover a descrição
    dados = ServicoAtualizacao(descricao=None)  # pyright: ignore[reportCallIssue]
    # Atualiza o serviço usando o Service
    resultado = atualizar_servico(
        servico.id_servico,
        dados,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert resultado.descricao is None

def test_atualizar_servico_inexistente(sessao_teste):
    # Cria estabelecimento sem serviços
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Cria dados para atualização
    dados = ServicoAtualizacao(preco=Decimal("45.00"))  # pyright: ignore[reportCallIssue]
    # Tenta atualizar serviço inexistente
    with pytest.raises(ServicoNaoEncontradoError):
        atualizar_servico(
            999,
            dados,
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_servico_de_outro_estabelecimento(sessao_teste):
    # Cria dois estabelecimentos e um serviço para o primeiro
    estabelecimento = criar_estabelecimento(sessao_teste)
    outro_estabelecimento = criar_outro_estabelecimento(sessao_teste)
    servico = cadastrar_servico(
        criar_dados_servico(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria dados para atualização
    dados = ServicoAtualizacao(preco=Decimal("45.00"))  # pyright: ignore[reportCallIssue]
    # Tenta atualizar o serviço usando o id do outro estabelecimento
    with pytest.raises(ServicoNaoEncontradoError):
        atualizar_servico(
            servico.id_servico,
            dados,
            outro_estabelecimento.id_estabelecimento,
            sessao_teste,
        )
    # Verifica que o serviço não foi alterado
    sessao_teste.refresh(servico)
    assert servico.preco == Decimal("35.00")
