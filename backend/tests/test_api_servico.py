import pytest
from app.core.tokens import criar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento
from fastapi.testclient import TestClient


# Cria estabelecimento pra teste
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
    # Salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

# Cria o cabeçalho de autenticação com o token do estabelecimento
def criar_cabecalho(estabelecimento):
    token = criar_token_acesso(estabelecimento.id_estabelecimento)
    return {"Authorization": f"Bearer {token}"}

# Cria dados para cadastro
def criar_dados_servico(nome="Corte de cabelo"):
    return {
        "nome": nome,
        "descricao": "Corte tradicional",
        "preco": "35.00",
        "duracao_minutos": 30,
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

# Fixture com o cabeçalho de um estabelecimento autenticado
@pytest.fixture
def cabecalho(sessao_teste):
    estabelecimento = criar_estabelecimento(sessao_teste)
    return criar_cabecalho(estabelecimento)

# Fixture com o cabeçalho de um segundo estabelecimento
# Usada pra testar que um estabelecimento não acessa serviços de outro
@pytest.fixture
def cabecalho_outro(sessao_teste):
    estabelecimento = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    return criar_cabecalho(estabelecimento)

def test_api_cadastrar_servico(cliente_teste, cabecalho):
    # Cria dados para cadastro
    dados = criar_dados_servico()
    # Envia requisição
    resposta = cliente_teste.post("/servicos", json=dados, headers=cabecalho)
    # Converte resposta para dicionário
    servico = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 201
    assert servico["id_servico"] > 0
    assert servico["id_estabelecimento"] > 0
    assert servico["nome"] == "Corte de cabelo"
    assert servico["descricao"] == "Corte tradicional"
    assert servico["preco"] == "35.00"
    assert servico["duracao_minutos"] == 30
    assert servico["ativo"] is True

def test_api_cadastrar_servico_sem_autenticacao(cliente_teste):
    # Cria dados para cadastro
    dados = criar_dados_servico()
    # Tenta cadastrar serviço sem token
    resposta = cliente_teste.post("/servicos", json=dados)
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_cadastrar_servico_token_invalido(cliente_teste):
    # Cria dados para cadastro
    dados = criar_dados_servico()
    # Tenta cadastrar serviço com token inválido
    resposta = cliente_teste.post(
        "/servicos",
        json=dados,
        headers={"Authorization": "Bearer token-invalido"},
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_cadastrar_servico_dados_invalidos(cliente_teste, cabecalho):
    # Cria dados com preço negativo
    dados = criar_dados_servico()
    dados["preco"] = "-10.00"
    # Tenta cadastrar serviço
    resposta = cliente_teste.post("/servicos", json=dados, headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_cadastrar_servico_ignora_id_estabelecimento(
    cliente_teste,
    cabecalho,
    cabecalho_outro,
):
    # Cria dados tentando cadastrar o serviço em outro estabelecimento
    dados = criar_dados_servico()
    dados["id_estabelecimento"] = 2
    # Envia requisição
    resposta = cliente_teste.post("/servicos", json=dados, headers=cabecalho)
    # Resultado esperado e comparações
    # O serviço é vinculado ao estabelecimento do token, não ao da requisição
    assert resposta.status_code == 201
    assert resposta.json()["id_estabelecimento"] == 1

def test_api_listar_servicos(cliente_teste, cabecalho):
    # Cadastra dois serviços
    cliente_teste.post(
        "/servicos",
        json=criar_dados_servico("Corte de cabelo"),
        headers=cabecalho,
    )
    cliente_teste.post(
        "/servicos",
        json=criar_dados_servico("Barba"),
        headers=cabecalho,
    )
    # Consulta os serviços
    resposta = cliente_teste.get("/servicos", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert [servico["nome"] for servico in resposta.json()] == [
        "Corte de cabelo",
        "Barba",
    ]

def test_api_listar_servicos_sem_cadastro(cliente_teste, cabecalho):
    # Consulta os serviços sem nenhum cadastrado
    resposta = cliente_teste.get("/servicos", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json() == []

def test_api_listar_servicos_sem_autenticacao(cliente_teste):
    # Tenta consultar os serviços sem token
    resposta = cliente_teste.get("/servicos")
    # Resultado esperado e comparações
    assert resposta.status_code == 401

def test_api_listar_servicos_apenas_do_estabelecimento(
    cliente_teste,
    cabecalho,
    cabecalho_outro,
):
    # Cadastra um serviço para cada estabelecimento
    cliente_teste.post(
        "/servicos",
        json=criar_dados_servico("Corte de cabelo"),
        headers=cabecalho,
    )
    cliente_teste.post(
        "/servicos",
        json=criar_dados_servico("Manicure"),
        headers=cabecalho_outro,
    )
    # Consulta os serviços do primeiro estabelecimento
    resposta = cliente_teste.get("/servicos", headers=cabecalho)
    # Resultado esperado e comparações
    # O serviço do outro estabelecimento não pode aparecer
    assert resposta.status_code == 200
    assert [servico["nome"] for servico in resposta.json()] == [
        "Corte de cabelo",
    ]

def test_api_consultar_servico(cliente_teste, cabecalho):
    # Cadastra serviço
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Consulta o serviço
    resposta = cliente_teste.get(f"/servicos/{id_servico}", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json() == cadastro.json()

def test_api_consultar_servico_inexistente(cliente_teste, cabecalho):
    # Tenta consultar serviço inexistente
    resposta = cliente_teste.get("/servicos/999", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Serviço não encontrado."

def test_api_consultar_servico_de_outro_estabelecimento(
    cliente_teste,
    cabecalho,
    cabecalho_outro,
):
    # Cadastra serviço para o primeiro estabelecimento
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Tenta consultar o serviço com o token do outro estabelecimento
    resposta = cliente_teste.get(
        f"/servicos/{id_servico}",
        headers=cabecalho_outro,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Serviço não encontrado."

def test_api_atualizar_servico(cliente_teste, cabecalho):
    # Cadastra serviço
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Atualiza apenas o preço
    resposta = cliente_teste.patch(
        f"/servicos/{id_servico}",
        json={"preco": "45.00"},
        headers=cabecalho,
    )
    # Converte resposta para dicionário
    servico = resposta.json()
    # Resultado esperado e comparações
    # Os campos não informados permanecem iguais
    assert resposta.status_code == 200
    assert servico["preco"] == "45.00"
    assert servico["nome"] == "Corte de cabelo"
    assert servico["duracao_minutos"] == 30
    assert servico["ativo"] is True

def test_api_inativar_servico(cliente_teste, cabecalho):
    # Cadastra serviço
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Inativa o serviço
    resposta = cliente_teste.patch(
        f"/servicos/{id_servico}",
        json={"ativo": False},
        headers=cabecalho,
    )
    # Consulta os serviços depois da inativação
    listagem = cliente_teste.get("/servicos", headers=cabecalho)
    # Resultado esperado e comparações
    # O serviço inativo continua aparecendo para o proprietário
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
    assert len(listagem.json()) == 1

def test_api_atualizar_servico_sem_campos(cliente_teste, cabecalho):
    # Cadastra serviço
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Tenta atualizar sem informar campos
    resposta = cliente_teste.patch(
        f"/servicos/{id_servico}",
        json={},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_servico_dados_invalidos(cliente_teste, cabecalho):
    # Cadastra serviço
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Tenta atualizar com duração zero
    resposta = cliente_teste.patch(
        f"/servicos/{id_servico}",
        json={"duracao_minutos": 0},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_servico_inexistente(cliente_teste, cabecalho):
    # Tenta atualizar serviço inexistente
    resposta = cliente_teste.patch(
        "/servicos/999",
        json={"preco": "45.00"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Serviço não encontrado."

def test_api_atualizar_servico_de_outro_estabelecimento(
    cliente_teste,
    cabecalho,
    cabecalho_outro,
):
    # Cadastra serviço para o primeiro estabelecimento
    cadastro = cliente_teste.post(
        "/servicos",
        json=criar_dados_servico(),
        headers=cabecalho,
    )
    id_servico = cadastro.json()["id_servico"]
    # Tenta atualizar o serviço com o token do outro estabelecimento
    resposta = cliente_teste.patch(
        f"/servicos/{id_servico}",
        json={"preco": "1.00"},
        headers=cabecalho_outro,
    )
    # Consulta o serviço com o token do dono
    consulta = cliente_teste.get(f"/servicos/{id_servico}", headers=cabecalho)
    # Resultado esperado e comparações
    # O serviço não pode ter sido alterado
    assert resposta.status_code == 404
    assert consulta.json()["preco"] == "35.00"

def test_api_atualizar_servico_sem_autenticacao(cliente_teste):
    # Tenta atualizar serviço sem token
    resposta = cliente_teste.patch("/servicos/1", json={"preco": "45.00"})
    # Resultado esperado e comparações
    assert resposta.status_code == 401
