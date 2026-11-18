import pytest
from fastapi.testclient import TestClient

from app.core.tokens import criar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento


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

# Cadastra estabelecimento pela API e retorna o cabeçalho de autenticação
def cadastrar_e_autenticar(cliente_teste, **kwargs):
    cadastro = cliente_teste.post(
        "/estabelecimentos",
        json=criar_dados_estabelecimento(**kwargs),
    )
    token = criar_token_acesso(cadastro.json()["id_estabelecimento"])
    return {"Authorization": f"Bearer {token}"}

def test_api_consultar_meu_estabelecimento(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Consulta os próprios dados
    resposta = cliente_teste.get("/estabelecimentos/me", headers=cabecalho)
    # Resultado esperado e comparações
    # Rota privada retorna os dados completos, sem a senha
    assert resposta.status_code == 200
    assert resposta.json()["identificador"] == "barbearia-joao"
    assert resposta.json()["email"] == "joao@example.com"
    assert "senha_hash" not in resposta.json()

def test_api_consultar_meu_estabelecimento_sem_autenticacao(cliente_teste):
    # Tenta consultar sem token
    resposta = cliente_teste.get("/estabelecimentos/me")
    # Resultado esperado e comparações
    # Não pode ser tratado como identificador público "me"
    assert resposta.status_code == 401

def test_api_atualizar_estabelecimento(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Atualiza apenas o endereço
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={"endereco": "Avenida Central, 200"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json()["endereco"] == "Avenida Central, 200"
    assert resposta.json()["nome"] == "Barbearia João"

def test_api_atualizar_estabelecimento_senha_permite_login(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Atualiza a senha
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={"senha": "NovaSenha456"},
        headers=cabecalho,
    )
    # Faz login com a senha nova e com a antiga
    login_novo = cliente_teste.post(
        "/auth/login",
        json={"email": "joao@example.com", "senha": "NovaSenha456"},
    )
    login_antigo = cliente_teste.post(
        "/auth/login",
        json={"email": "joao@example.com", "senha": "Senha123"},
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert "senha" not in resposta.json()
    assert login_novo.status_code == 200
    assert login_antigo.status_code == 401

def test_api_atualizar_estabelecimento_identificador_publico(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Troca o identificador
    cliente_teste.patch(
        "/estabelecimentos/me",
        json={"identificador": "barbearia-do-joao"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    # A página pública passa a responder no identificador novo
    assert cliente_teste.get("/estabelecimentos/barbearia-do-joao").status_code == 200
    assert cliente_teste.get("/estabelecimentos/barbearia-joao").status_code == 404

def test_api_atualizar_estabelecimento_duplicado(cliente_teste):
    # Cadastra dois estabelecimentos
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    cadastrar_e_autenticar(
        cliente_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    # Tenta usar o e-mail do outro estabelecimento
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={"email": "maria@example.com"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "E-mail já cadastrado."

def test_api_atualizar_estabelecimento_dados_invalidos(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Tenta enviar documento sem o tipo
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={"documento": "98765432100"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_estabelecimento_sem_campos(cliente_teste):
    # Cadastra e autentica
    cabecalho = cadastrar_e_autenticar(cliente_teste)
    # Tenta atualizar sem informar campos
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_estabelecimento_sem_autenticacao(cliente_teste):
    # Tenta atualizar sem token
    resposta = cliente_teste.patch(
        "/estabelecimentos/me",
        json={"nome": "Outro nome"},
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 401
