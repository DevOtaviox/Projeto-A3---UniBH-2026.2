import pytest
from app.core.tokens import criar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento
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
    # Yield da sessão de teste ao invés da sessão real
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

def test_api_cadastrar_estabelecimento_identificador_invalido(cliente_teste):
    # Cria dados com identificador inválido
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "12345678901",
        "identificador": "barbearia--joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Envia requisição de cadastro
    resposta = cliente_teste.post("/estabelecimentos", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_consultar_estabelecimento_publico(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Consulta o estabelecimento pelo identificador
    resposta = cliente_teste.get("/estabelecimentos/barbearia-joao")
    # Converte resposta para dicionário
    estabelecimento = resposta.json()
    # Resultado esperado e comparações
    assert cadastro.status_code == 201
    assert resposta.status_code == 200
    assert estabelecimento["id_estabelecimento"] == cadastro.json()["id_estabelecimento"]
    assert estabelecimento["nome"] == "Barbearia João"
    assert estabelecimento["endereco"] == "Rua das Flores, 100"
    assert estabelecimento["imagem"] is None
    assert estabelecimento["identificador"] == "barbearia-joao"
    # Verifica ausência de informações privadas
    assert "tipo_documento" not in estabelecimento
    assert "documento" not in estabelecimento
    assert "email" not in estabelecimento
    assert "senha_hash" not in estabelecimento
    assert "ativo" not in estabelecimento

def test_api_consultar_estabelecimento_publico_inexistente(cliente_teste):
    # Consulta um estabelecimento inexistente
    resposta = cliente_teste.get("/estabelecimentos/barbearia-inexistente")
    # Resultado esperado e comparações
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Estabelecimento não encontrado."

def test_api_consultar_estabelecimento_publico_inativo(cliente_teste, sessao_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Busca o estabelecimento no db e desativa
    id_estabelecimento = cadastro.json()["id_estabelecimento"]
    estabelecimento = sessao_teste.get(Estabelecimento, id_estabelecimento)
    assert estabelecimento is not None
    estabelecimento.ativo = False
    sessao_teste.commit()
    # Tenta consultar
    resposta = cliente_teste.get("/estabelecimentos/barbearia-joao")
    # Resultado esperado e comparações
    assert cadastro.status_code == 201
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Estabelecimento não encontrado."

# Cria cabeçalho de autenticação para o estabelecimento
def criar_cabecalho(id_estabelecimento):
    token = criar_token_acesso(id_estabelecimento)
    return {"Authorization": f"Bearer {token}"}

def test_api_atualizar_estabelecimento(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados para atualização e cabeçalho de autenticação
    dados_atualizacao = {
        "nome": "Barbearia Teste",
        "endereco": "Avenida Teste, 200",
    }
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Atualiza o estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json=dados_atualizacao,
        headers=cabecalho,
    )
    # Converte resposta para dicionário
    estabelecimento = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert estabelecimento["nome"] == "Barbearia Teste"
    assert estabelecimento["endereco"] == "Avenida Teste, 200"
    assert estabelecimento["documento"] == "12345678901"
    assert estabelecimento["identificador"] == "barbearia-joao"
    assert estabelecimento["email"] == "joao@example.com"

def test_api_atualizar_estabelecimento_sem_autenticacao(cliente_teste):
    # Cria dados para atualização
    dados = {
        "nome": "Barbearia Teste",
    }
    # Tenta atualizar sem token
    resposta = cliente_teste.patch("/estabelecimentos/me", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_atualizar_estabelecimento_documento_duplicado(cliente_teste):
    # Cadastra dois estabelecimentos
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    dados_outro = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    cliente_teste.post("/estabelecimentos", json=dados_outro)
    # Cria dados com documento já cadastrado
    dados_atualizacao = {
        "tipo_documento": "CPF",
        "documento": "98765432100",
    }
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Tenta atualizar o estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json=dados_atualizacao,
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Documento já cadastrado."

def test_api_atualizar_estabelecimento_dados_invalidos(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados com nome vazio
    dados_atualizacao = {
        "nome": "",
    }
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Tenta atualizar o estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json=dados_atualizacao,
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_estabelecimento_email_nao_permitido(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados tentando alterar o e-mail
    dados_atualizacao = {
        "email": "novo@example.com",
    }
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Tenta atualizar o estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json=dados_atualizacao,
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_estabelecimento_ativo_nao_permitido(cliente_teste):
    # Cadastra um estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria dados tentando inativar o estabelecimento
    dados_atualizacao = {
        "ativo": False,
    }
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Tenta atualizar o estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json=dados_atualizacao,
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_consultar_estabelecimento_atual(cliente_teste):
    # Cadastra  estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria cabeçalho de autenticação
    cabecalho = criar_cabecalho(cadastro.json()["id_estabelecimento"])
    # Consulta o estabelecimento autenticado
    resposta = cliente_teste.get("/estabelecimentos/me", headers=cabecalho)
    # Converte resposta para dicionário
    estabelecimento = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert estabelecimento["id_estabelecimento"] == cadastro.json()["id_estabelecimento"]
    assert estabelecimento["nome"] == "Barbearia João"
    assert estabelecimento["endereco"] == "Rua das Flores, 100"
    assert estabelecimento["documento"] == "12345678901"
    assert estabelecimento["identificador"] == "barbearia-joao"
    assert estabelecimento["email"] == "joao@example.com"
    assert estabelecimento["ativo"] is True
    # Verifica ausência de senha
    assert "senha" not in estabelecimento
    assert "senha_hash" not in estabelecimento

def test_api_consultar_estabelecimento_atual_sem_autenticacao(cliente_teste):
    # Tenta consultar os dados sem token
    resposta = cliente_teste.get("/estabelecimentos/me")
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_consultar_estabelecimento_atual_token_invalido(cliente_teste):
    # Cria header com token inválido
    cabecalho = {
        "Authorization": "Bearer token-invalido",
    }
    # Tenta consultar os dados
    resposta = cliente_teste.get("/estabelecimentos/me", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_consultar_estabelecimento_atual_inativo(cliente_teste, sessao_teste):
    # Cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastro = cliente_teste.post("/estabelecimentos", json=dados)
    # Cria header
    id_estabelecimento = cadastro.json()["id_estabelecimento"]
    cabecalho = criar_cabecalho(id_estabelecimento)
    # Busca o estabelecimento no db e desativa
    estabelecimento = sessao_teste.get(Estabelecimento, id_estabelecimento)
    assert estabelecimento is not None
    estabelecimento.ativo = False
    sessao_teste.commit()
    # Tenta consultar o estabelecimento
    resposta = cliente_teste.get("/estabelecimentos/me", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 401
