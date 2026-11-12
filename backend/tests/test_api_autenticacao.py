import pytest
from app.core.security import gerar_hash_senha
from app.core.tokens import validar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento
from fastapi.testclient import TestClient


# Cria estabelecimento pra teste
def criar_estabelecimento(
    sessao_teste,
    email="joao@example.com",
    senha="Senha123",
    ativo=True,
):
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        email=email,
        senha_hash=gerar_hash_senha(senha),
        ativo=ativo,
    )
    # Salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

# Cria client de teste com db temporário ad fixture
@pytest.fixture
def cliente_teste(sessao_teste):
    # Yield da sessão de teste ao invés da sessão real
    def obter_sessao_teste():
        yield sessao_teste
    # Override para usar o teste no lugar do real
    app.dependency_overrides[obter_sessao_banco] = obter_sessao_teste
    # Cria client de teste
    cliente = TestClient(app)
    try:
        yield cliente
    finally:
        # Fecha o client de teste
        cliente.close()
        # Remove o override
        app.dependency_overrides.pop(obter_sessao_banco, None)

def test_api_login_estabelecimento(cliente_teste, sessao_teste):
    # Cria estabelecimento
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Dados para autenticação
    dados = {
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Envia requisição pro endpoint de login
    resposta = cliente_teste.post("/auth/login", json=dados)
    # Converte resposta para dicionário
    resultado = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert isinstance(resultado["access_token"], str)
    assert resultado["token_type"] == "bearer"
    # Verifica se o token corresponde ao estabelecimento
    id_estabelecimento = validar_token_acesso(resultado["access_token"])
    assert id_estabelecimento == estabelecimento.id_estabelecimento

def test_api_login_email_inexistente(cliente_teste):
    # Cria dados com e-mail inexistente
    dados = {
        "email": "inexistente@example.com",
        "senha": "Senha123",
    }
    # Tenta autenticar
    resposta = cliente_teste.post("/auth/login", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha incorretos."

def test_api_login_senha_incorreta(cliente_teste, sessao_teste):
    # Cria estabelecimento
    criar_estabelecimento(sessao_teste)
    # Cria dados com senha incorreta
    dados = {
        "email": "joao@example.com",
        "senha": "Senha321",
    }
    # Tenta autenticar
    resposta = cliente_teste.post("/auth/login", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha incorretos."

def test_api_login_estabelecimento_inativo(cliente_teste, sessao_teste):
    # Cria estabelecimento inativo
    criar_estabelecimento(sessao_teste, ativo=False)
    # Cria dados para autenticação
    dados = {
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Tenta autenticar
    resposta = cliente_teste.post("/auth/login", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha incorretos."

def test_api_login_dados_invalidos(cliente_teste):
    # Cria dados com e-mail inválido
    dados = {
        "email": "joao",
        "senha": "Senha123",
    }
    # Tenta autenticar
    resposta = cliente_teste.post("/auth/login", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 422
