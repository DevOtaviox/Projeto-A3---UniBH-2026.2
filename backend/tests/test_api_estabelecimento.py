import pytest
from app.db.session import obter_sessao_banco
from app.main import app
from fastapi.testclient import TestClient


# Cria dados para cadastro
def criar_dados_estabelecimento(
    email="joao@example.com",
    documento="12345678901",
    identificador="barbearia-joao",
):
    return {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": documento,
        "identificador": identificador,
        "email": email,
        "senha": "Senha123",
    }

# Fixture pra client de teste usando a sessão do conftest.py
@pytest.fixture
def cliente_teste(sessao_teste):
    # Substitui a dependência de sessão pela sessão temporária
    def obter_sessao_teste():
        yield sessao_teste
    # Override pra usar o db de teste ao invés do db real
    app.dependency_overrides[obter_sessao_banco] = obter_sessao_teste
    # Cria cliente de testes
    cliente = TestClient(app)
    try:
        yield cliente
    finally:
        # Fecha o client e remove override
        cliente.close()
        app.dependency_overrides.pop(obter_sessao_banco, None)

def test_api_cadastrar_estabelecimento(cliente_teste):
    # Cria dados para cadastro
    dados = criar_dados_estabelecimento()
    # Envia requisição
    resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Converte resposta para dicionário
    estabelecimento = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 201
    assert estabelecimento["id_estabelecimento"] > 0
    assert estabelecimento["nome"] == "Barbearia João"
    assert estabelecimento["endereco"] == "Rua das Flores, 100"
    assert estabelecimento["tipo_documento"] == "CPF"
    assert estabelecimento["documento"] == "12345678901"
    assert estabelecimento["identificador"] == "barbearia-joao"
    assert estabelecimento["email"] == "joao@example.com"
    assert estabelecimento["ativo"] is True
    # Verifica ausencia de senha
    assert "senha" not in estabelecimento
    assert "senha_hash" not in estabelecimento

def test_api_cadastrar_estabelecimento_email_duplicado(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    primeira_resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados com e-mail duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="joao@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    # Tenta cadastrar estabelecimento com e-mail duplicado
    resposta = cliente_teste.post("/estabelecimentos", json=dados_duplicados)
    # Resultado esperado e comparações
    assert primeira_resposta.status_code == 201
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "E-mail já cadastrado."

def test_api_cadastrar_estabelecimento_documento_duplicado(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    primeira_resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados com documento duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="12345678901",
        identificador="manicure-maria",
    )
    # Tenta cadastrar estabelecimento
    resposta = cliente_teste.post("/estabelecimentos", json=dados_duplicados)
    # Resultado esperado e comparações
    assert primeira_resposta.status_code == 201
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Documento já cadastrado."

def test_api_cadastrar_estabelecimento_identificador_duplicado(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    primeira_resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados com identificador duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="98765432100",
        identificador="barbearia-joao",
    )
    # Tenta cadastrar estabeleciment
    resposta = cliente_teste.post("/estabelecimentos", json=dados_duplicados)
    # Resultado esperado e comparações
    assert primeira_resposta.status_code == 201
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Identificador já cadastrado."

def test_api_cadastrar_estabelecimento_dados_invalidos(cliente_teste):
    # Cria dados com senha menor que oito caracteres
    dados = criar_dados_estabelecimento()
    dados["senha"] = "1234567"
    # Tenta cadastrar estabelecimento
    resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 422
