import pytest
from app.core.security import verificar_senha
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import EstabelecimentoCriacao
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    cadastrar_estabelecimento,
)
from sqlalchemy.orm import sessionmaker


# Cria dados para cadastro
def criar_dados_estabelecimento(
    email="joao@example.com",
    documento="12345678901",
    identificador="barbearia-joao",
):
    return EstabelecimentoCriacao(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento=documento,
        identificador=identificador,
        email=email,
        senha="Senha123",
    )

def test_cadastrar_estabelecimento(sessao_teste):
    # Cria dados para cadastro
    dados = criar_dados_estabelecimento()
    # Cadastra o estabelecimento usando o Service
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Cria um gerador de sessões para consulta
    gerador_sessoes = sessionmaker(bind=sessao_teste.get_bind())
    with gerador_sessoes() as sessao_consulta:
        estabelecimento_salvo = sessao_consulta.get(
            Estabelecimento,
            estabelecimento.id_estabelecimento,
        )
    # Resultado esperado e comparações
    assert estabelecimento_salvo is not None
    assert estabelecimento_salvo.nome == "Barbearia João"
    assert estabelecimento_salvo.endereco == "Rua das Flores, 100"
    assert estabelecimento_salvo.tipo_documento == "CPF"
    assert estabelecimento_salvo.documento == "12345678901"
    assert estabelecimento_salvo.identificador == "barbearia-joao"
    assert estabelecimento_salvo.email == "joao@example.com"
    assert estabelecimento_salvo.ativo is True

def test_cadastrar_estabelecimento_hashing(sessao_teste):
    # Cria dados para cadastro
    dados = criar_dados_estabelecimento()
    # Cadastra o estabelecimento usando o Service
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Verifica hash da senha
    assert estabelecimento.senha_hash != dados.senha
    assert verificar_senha(dados.senha, estabelecimento.senha_hash) is True

def test_cadastrar_estabelecimento_email_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com e-mail duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="joao@example.com",
        documento="98765432100",
        identificador="barbearia-maria",
    )
    # Tenta cadastrar estabelecimento com e-mail duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)

def test_cadastrar_estabelecimento_documento_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com documento duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="12345678901",
        identificador="barbearia-maria",
    )
    # Tenta cadastrar estabelecimento com documento duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)

def test_cadastrar_estabelecimento_identificador_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com identificador duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="98765432100",
        identificador="barbearia-joao",
    )
    # Tenta cadastrar estabelecimento com identificador duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)
