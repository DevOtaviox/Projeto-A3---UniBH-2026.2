from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.tokens import criar_token_acesso
from app.db.session import obter_sessao_banco
from app.main import app
from app.models.estabelecimento import Estabelecimento
from app.models.horario_funcionamento import HorarioFuncionamento
from app.models.servico import Servico
from app.services.agendamento import DIAS_SEMANA

# Usa sempre datas futuras pra não depender da hora em que o teste roda
AMANHA = date.today() + timedelta(days=1)


# Cria estabelecimento com horário (todos os dias, 09:00-18:00, almoço 12:00-13:00)
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
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    horario = HorarioFuncionamento(
        id_estabelecimento=estabelecimento.id_estabelecimento,
        **{dia: True for dia in DIAS_SEMANA},
        hora_abertura=time(9, 0),
        hora_fechamento=time(18, 0),
        inicio_intervalo=time(12, 0),
        fim_intervalo=time(13, 0),
    )
    sessao_teste.add(horario)
    sessao_teste.commit()
    return estabelecimento

# Cria serviço de teste
def criar_servico(sessao_teste, estabelecimento, duracao=30, ativo=True):
    servico = Servico(
        id_estabelecimento=estabelecimento.id_estabelecimento,
        nome="Corte",
        preco=Decimal("35.00"),
        duracao_minutos=duracao,
        ativo=ativo,
    )
    sessao_teste.add(servico)
    sessao_teste.commit()
    sessao_teste.refresh(servico)
    return servico

# Cria o cabeçalho de autenticação com o token do estabelecimento
def criar_cabecalho(estabelecimento):
    token = criar_token_acesso(estabelecimento.id_estabelecimento)
    return {"Authorization": f"Bearer {token}"}

# Cria dados para cadastro de agendamento
def criar_dados(id_servico, inicio="09:00", data_agendamento=AMANHA):
    return {
        "id_servico": id_servico,
        "nome_cliente": "Carlos Silva",
        "telefone_cliente": "31999998888",
        "data_agendamento": data_agendamento.isoformat(),
        "horario_inicio": inicio,
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

# Cenário padrão: estabelecimento com horário, um serviço de 30 min e o token
@pytest.fixture
def cenario(sessao_teste):
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = criar_servico(sessao_teste, estabelecimento)
    return servico.id_servico, criar_cabecalho(estabelecimento)

# Cenário de um segundo estabelecimento
@pytest.fixture
def cenario_outro(sessao_teste):
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    servico = criar_servico(sessao_teste, outro)
    return servico.id_servico, criar_cabecalho(outro)

URL_PUBLICA = "/estabelecimentos/barbearia-joao"
# Corpo do PATCH de cancelamento (única alteração permitida pelo schema)
CANCELAMENTO = {"status": "cancelado"}


# ---------- Público: disponibilidade

def test_api_disponibilidade(cliente_teste, cenario):
    id_servico, _ = cenario
    resposta = cliente_teste.get(
        f"{URL_PUBLICA}/disponibilidade",
        params={"id_servico": id_servico, "data": AMANHA.isoformat()},
    )
    dados = resposta.json()
    assert resposta.status_code == 200
    assert dados["id_servico"] == id_servico
    assert dados["data_agendamento"] == AMANHA.isoformat()
    assert dados["duracao_minutos"] == 30
    assert dados["horarios"][0] == "09:00:00"
    assert "12:00:00" not in dados["horarios"]
    assert dados["horarios"][-1] == "17:30:00"

def test_api_disponibilidade_apos_agendamento(cliente_teste, cenario):
    id_servico, _ = cenario
    cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico, "10:00"))
    resposta = cliente_teste.get(
        f"{URL_PUBLICA}/disponibilidade",
        params={"id_servico": id_servico, "data": AMANHA.isoformat()},
    )
    horarios = resposta.json()["horarios"]
    assert "10:00:00" not in horarios
    assert "09:30:00" in horarios
    assert "10:30:00" in horarios

def test_api_disponibilidade_estabelecimento_inexistente(cliente_teste):
    resposta = cliente_teste.get(
        "/estabelecimentos/inexistente/disponibilidade",
        params={"id_servico": 1, "data": AMANHA.isoformat()},
    )
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Estabelecimento não encontrado."

def test_api_disponibilidade_servico_de_outro_estabelecimento(cliente_teste, cenario, cenario_outro):
    id_servico_outro, _ = cenario_outro
    resposta = cliente_teste.get(
        f"{URL_PUBLICA}/disponibilidade",
        params={"id_servico": id_servico_outro, "data": AMANHA.isoformat()},
    )
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Serviço não encontrado."

def test_api_disponibilidade_sem_parametros(cliente_teste, cenario):
    resposta = cliente_teste.get(f"{URL_PUBLICA}/disponibilidade")
    assert resposta.status_code == 422


# ---------- Público: agendar

def test_api_agendar_publico(cliente_teste, cenario):
    id_servico, _ = cenario
    resposta = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    dados = resposta.json()
    assert resposta.status_code == 201
    assert dados["id_agendamento"] > 0
    assert dados["horario_inicio"] == "09:00:00"
    assert dados["horario_fim"] == "09:30:00"
    assert dados["status"] == "agendado"
    assert dados["data_cancelamento"] is None

def test_api_agendar_publico_horario_ocupado(cliente_teste, cenario):
    id_servico, _ = cenario
    cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico, "10:00"))
    resposta = cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(id_servico, "10:10"),
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Este horário não está mais disponível. Escolha outro horário."
    )

def test_api_agendar_publico_horario_invalido(cliente_teste, cenario):
    id_servico, _ = cenario
    resposta = cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(id_servico, "12:10"),
    )
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "O horário coincide com o intervalo do estabelecimento."

def test_api_agendar_publico_alem_de_30_dias(cliente_teste, cenario):
    id_servico, _ = cenario
    data_distante = date.today() + timedelta(days=31)
    resposta = cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(id_servico, data_agendamento=data_distante),
    )
    assert resposta.status_code == 422
    assert "30 dias" in resposta.json()["detail"][0]["msg"]

def test_api_agendar_publico_dados_invalidos(cliente_teste, cenario):
    id_servico, _ = cenario
    dados = criar_dados(id_servico)
    dados["telefone_cliente"] = "123"
    resposta = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=dados)
    assert resposta.status_code == 422

def test_api_agendar_publico_servico_inativo(cliente_teste, sessao_teste, cenario):
    estabelecimento = sessao_teste.query(Estabelecimento).first()
    inativo = criar_servico(sessao_teste, estabelecimento, ativo=False)
    resposta = cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(inativo.id_servico),
    )
    assert resposta.status_code == 404

def test_api_agendar_publico_servico_de_outro_estabelecimento(cliente_teste, cenario, cenario_outro):
    id_servico_outro, _ = cenario_outro
    resposta = cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(id_servico_outro),
    )
    assert resposta.status_code == 404


# ---------- Proprietário

def test_api_criar_agendamento_proprietario(cliente_teste, cenario):
    id_servico, cabecalho = cenario
    resposta = cliente_teste.post(
        "/agendamentos",
        json=criar_dados(id_servico, "15:00"),
        headers=cabecalho,
    )
    assert resposta.status_code == 201
    assert resposta.json()["horario_fim"] == "15:30:00"

def test_api_criar_agendamento_servico_de_outro_estabelecimento(cliente_teste, cenario, cenario_outro):
    _, cabecalho = cenario
    id_servico_outro, _ = cenario_outro
    resposta = cliente_teste.post(
        "/agendamentos",
        json=criar_dados(id_servico_outro),
        headers=cabecalho,
    )
    assert resposta.status_code == 404

def test_api_listar_agendamentos(cliente_teste, cenario, cenario_outro):
    id_servico, cabecalho = cenario
    id_servico_outro, _ = cenario_outro
    cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico, "15:00"))
    cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico, "09:00"))
    cliente_teste.post(
        "/estabelecimentos/manicure-maria/agendamentos",
        json=criar_dados(id_servico_outro, "09:00"),
    )
    resposta = cliente_teste.get("/agendamentos", headers=cabecalho)
    assert resposta.status_code == 200
    # Só os do próprio estabelecimento, ordenados pelo horário
    assert [a["horario_inicio"] for a in resposta.json()] == ["09:00:00", "15:00:00"]

def test_api_listar_agendamentos_filtros(cliente_teste, cenario):
    id_servico, cabecalho = cenario
    depois_de_amanha = AMANHA + timedelta(days=1)
    primeiro = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    cliente_teste.post(
        f"{URL_PUBLICA}/agendamentos",
        json=criar_dados(id_servico, data_agendamento=depois_de_amanha),
    )
    cliente_teste.patch(
        f"/agendamentos/{primeiro.json()['id_agendamento']}",
        json=CANCELAMENTO,
        headers=cabecalho,
    )
    por_data = cliente_teste.get(
        "/agendamentos",
        params={"data": depois_de_amanha.isoformat()},
        headers=cabecalho,
    )
    cancelados = cliente_teste.get(
        "/agendamentos",
        params={"status": "cancelado"},
        headers=cabecalho,
    )
    status_invalido = cliente_teste.get(
        "/agendamentos",
        params={"status": "pendente"},
        headers=cabecalho,
    )
    assert [a["data_agendamento"] for a in por_data.json()] == [depois_de_amanha.isoformat()]
    assert [a["id_agendamento"] for a in cancelados.json()] == [primeiro.json()["id_agendamento"]]
    assert status_invalido.status_code == 422

def test_api_consultar_agendamento(cliente_teste, cenario, cenario_outro):
    id_servico, cabecalho = cenario
    _, cabecalho_outro = cenario_outro
    cadastro = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    url = f"/agendamentos/{cadastro.json()['id_agendamento']}"
    resposta = cliente_teste.get(url, headers=cabecalho)
    resposta_outro = cliente_teste.get(url, headers=cabecalho_outro)
    assert resposta.status_code == 200
    assert resposta.json() == cadastro.json()
    # Outro estabelecimento não enxerga o agendamento
    assert resposta_outro.status_code == 404
    assert resposta_outro.json()["detail"] == "Agendamento não encontrado."

def test_api_cancelar_agendamento_de_outro_estabelecimento(cliente_teste, cenario, cenario_outro):
    id_servico, _ = cenario
    _, cabecalho_outro = cenario_outro
    cadastro = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    resposta = cliente_teste.patch(
        f"/agendamentos/{cadastro.json()['id_agendamento']}",
        json=CANCELAMENTO,
        headers=cabecalho_outro,
    )
    assert resposta.status_code == 404

def test_api_agendamentos_sem_autenticacao(cliente_teste, cenario):
    id_servico, _ = cenario
    assert cliente_teste.get("/agendamentos").status_code == 401
    assert cliente_teste.post("/agendamentos", json=criar_dados(id_servico)).status_code == 401
    assert cliente_teste.get("/agendamentos/1").status_code == 401
    assert cliente_teste.patch("/agendamentos/1", json=CANCELAMENTO).status_code == 401

def test_api_cancelar_agendamento(cliente_teste, cenario):
    id_servico, cabecalho = cenario
    cadastro = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    url = f"/agendamentos/{cadastro.json()['id_agendamento']}"
    resposta = cliente_teste.patch(url, json=CANCELAMENTO, headers=cabecalho)
    de_novo = cliente_teste.patch(url, json=CANCELAMENTO, headers=cabecalho)
    # Cancelamento libera o horário para outro cliente
    novo = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelado"
    assert resposta.json()["data_cancelamento"] is not None
    assert de_novo.status_code == 409
    assert de_novo.json()["detail"] == "Este agendamento já está cancelado."
    assert novo.status_code == 201

def test_api_cancelar_agendamento_inexistente(cliente_teste, cenario):
    _, cabecalho = cenario
    resposta = cliente_teste.patch("/agendamentos/999", json=CANCELAMENTO, headers=cabecalho)
    assert resposta.status_code == 404

@pytest.mark.parametrize(
    "corpo",
    [{}, {"status": "agendado"}, {"horario_inicio": "10:00"}],
)
def test_api_alterar_agendamento_apenas_cancelamento(cliente_teste, cenario, corpo):
    # Reagendar ou reativar não é permitido, só cancelar
    id_servico, cabecalho = cenario
    cadastro = cliente_teste.post(f"{URL_PUBLICA}/agendamentos", json=criar_dados(id_servico))
    resposta = cliente_teste.patch(
        f"/agendamentos/{cadastro.json()['id_agendamento']}",
        json=corpo,
        headers=cabecalho,
    )
    assert resposta.status_code == 422
