import pytest
from fastapi.testclient import TestClient

from app.core.tokens import criar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento


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

# Cria dados de horário: segunda a sexta, 09:00 às 18:00, almoço 12:00 às 13:00
def criar_dados_horario():
    return {
        "segunda": True,
        "terca": True,
        "quarta": True,
        "quinta": True,
        "sexta": True,
        "hora_abertura": "09:00",
        "hora_fechamento": "18:00",
        "inicio_intervalo": "12:00",
        "fim_intervalo": "13:00",
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
    return criar_cabecalho(criar_estabelecimento(sessao_teste))

def test_api_configurar_horario(cliente_teste, cabecalho):
    # Configura o horário
    resposta = cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
        headers=cabecalho,
    )
    # Converte resposta para dicionário
    horario = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert horario["id_horario"] > 0
    assert horario["segunda"] is True
    assert horario["domingo"] is False
    assert horario["hora_abertura"] == "09:00:00"
    assert horario["fim_intervalo"] == "13:00:00"

def test_api_consultar_horario(cliente_teste, cabecalho):
    # Configura e consulta o horário
    cadastro = cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
        headers=cabecalho,
    )
    resposta = cliente_teste.get("/horario-funcionamento", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json() == cadastro.json()

def test_api_consultar_horario_nao_configurado(cliente_teste, cabecalho):
    # Consulta sem ter configurado
    resposta = cliente_teste.get("/horario-funcionamento", headers=cabecalho)
    # Resultado esperado e comparações
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Horário de funcionamento não configurado."

def test_api_configurar_horario_invalido(cliente_teste, cabecalho):
    # Cria dados com abertura depois do fechamento
    dados = criar_dados_horario()
    dados["hora_abertura"] = "19:00"
    # Tenta configurar
    resposta = cliente_teste.put(
        "/horario-funcionamento",
        json=dados,
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422

def test_api_atualizar_horario(cliente_teste, cabecalho):
    # Configura o horário
    cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
        headers=cabecalho,
    )
    # Abre também no sábado
    resposta = cliente_teste.patch(
        "/horario-funcionamento",
        json={"sabado": True},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json()["sabado"] is True
    assert resposta.json()["segunda"] is True

def test_api_atualizar_horario_resultado_invalido(cliente_teste, cabecalho):
    # Configura o horário até 18:00
    cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
        headers=cabecalho,
    )
    # Tenta abrir depois do fechamento atual
    resposta = cliente_teste.patch(
        "/horario-funcionamento",
        json={"hora_abertura": "19:00"},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "A abertura deve ser anterior ao fechamento."

def test_api_atualizar_horario_nao_configurado(cliente_teste, cabecalho):
    # Tenta atualizar sem ter configurado
    resposta = cliente_teste.patch(
        "/horario-funcionamento",
        json={"sabado": True},
        headers=cabecalho,
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 404

def test_api_horario_apenas_do_estabelecimento(cliente_teste, sessao_teste, cabecalho):
    # Configura horário para o primeiro estabelecimento
    cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
        headers=cabecalho,
    )
    # Consulta com o token de outro estabelecimento
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    resposta = cliente_teste.get(
        "/horario-funcionamento",
        headers=criar_cabecalho(outro),
    )
    # Resultado esperado e comparações
    assert resposta.status_code == 404

def test_api_horario_sem_autenticacao(cliente_teste):
    # Tenta acessar sem token
    assert cliente_teste.get("/horario-funcionamento").status_code == 401
    assert cliente_teste.put(
        "/horario-funcionamento",
        json=criar_dados_horario(),
    ).status_code == 401
    assert cliente_teste.patch(
        "/horario-funcionamento",
        json={"sabado": True},
    ).status_code == 401
