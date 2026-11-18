from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest

from app.models.estabelecimento import Estabelecimento
from app.models.horario_funcionamento import HorarioFuncionamento
from app.models.servico import Servico
from app.schemas.agendamento import AgendamentoCriacao
from app.services.agendamento import (
    DIAS_SEMANA,
    AgendamentoCanceladoError,
    AgendamentoInvalidoError,
    AgendamentoNaoEncontradoError,
    HorarioIndisponivelError,
    cadastrar_agendamento,
    cadastrar_agendamento_publico,
    cancelar_agendamento,
    consultar_disponibilidade,
    listar_agendamentos,
    obter_agendamento,
    verificar_regras_horario,
)
from app.services.estabelecimento import EstabelecimentoNaoEncontradoError
from app.services.servico import ServicoNaoEncontradoError

# As datas são relativas ao dia de hoje, porque o schema não aceita datas passadas
# "agora" é fixado às 08:00 de hoje pra os testes não dependerem da hora atual
HOJE = date.today()
AMANHA = HOJE + timedelta(days=1)
AGORA = datetime.combine(HOJE, time(8, 0))


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
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

# Cria horário: todos os dias, 09:00 às 18:00, almoço 12:00 às 13:00
# Todos os dias abertos pra os testes não dependerem do dia da semana
def criar_horario(sessao_teste, estabelecimento, **alteracoes):
    dados = {dia: True for dia in DIAS_SEMANA}
    dados.update(
        hora_abertura=time(9, 0),
        hora_fechamento=time(18, 0),
        inicio_intervalo=time(12, 0),
        fim_intervalo=time(13, 0),
    )
    dados.update(alteracoes)
    horario = HorarioFuncionamento(
        id_estabelecimento=estabelecimento.id_estabelecimento,
        **dados,
    )
    sessao_teste.add(horario)
    sessao_teste.commit()
    return horario

# Cria serviço de teste
def criar_servico(sessao_teste, estabelecimento, duracao=30, ativo=True, nome="Corte"):
    servico = Servico(
        id_estabelecimento=estabelecimento.id_estabelecimento,
        nome=nome,
        preco=Decimal("35.00"),
        duracao_minutos=duracao,
        ativo=ativo,
    )
    sessao_teste.add(servico)
    sessao_teste.commit()
    sessao_teste.refresh(servico)
    return servico

# Cria dados para cadastro de agendamento
def criar_dados(servico, inicio=time(9, 0), data_agendamento=AMANHA):
    return AgendamentoCriacao(
        id_servico=servico.id_servico,
        nome_cliente="Carlos Silva",
        telefone_cliente="31999998888",
        data_agendamento=data_agendamento,
        horario_inicio=inicio,
    )

# Monta o cenário padrão: estabelecimento com horário e um serviço de 30 min
@pytest.fixture
def cenario(sessao_teste):
    estabelecimento = criar_estabelecimento(sessao_teste)
    horario = criar_horario(sessao_teste, estabelecimento)
    servico = criar_servico(sessao_teste, estabelecimento)
    return estabelecimento, horario, servico

# Atalho pra cadastrar um agendamento no cenário
def agendar(sessao_teste, estabelecimento, servico, inicio=time(9, 0), data_agendamento=AMANHA):
    return cadastrar_agendamento(
        criar_dados(servico, inicio, data_agendamento),
        estabelecimento.id_estabelecimento,
        sessao_teste,
        agora=AGORA,
    )


# ---------- Regras de horário

def test_regras_horario_valido(cenario):
    _, horario, _ = cenario
    assert verificar_regras_horario(horario, AMANHA, time(9, 0), 30, AGORA) is None

@pytest.mark.parametrize(
    ("inicio", "duracao", "trecho"),
    [
        (time(8, 50), 30, "fora do funcionamento"),
        (time(17, 40), 30, "fora do funcionamento"),
        (time(9, 5), 30, "intervalos de 10 minutos"),
        (time(11, 40), 30, "intervalo do estabelecimento"),
        (time(12, 30), 10, "intervalo do estabelecimento"),
        (time(9, 0, 30), 30, "horas e minutos"),
    ],
)
def test_regras_horario_invalido(cenario, inicio, duracao, trecho):
    _, horario, _ = cenario
    motivo = verificar_regras_horario(horario, AMANHA, inicio, duracao, AGORA)
    assert motivo is not None
    assert trecho in motivo

def test_regras_horario_termina_no_fechamento(cenario):
    # Um serviço de 30 min às 17:30 termina exatamente no fechamento
    _, horario, _ = cenario
    assert verificar_regras_horario(horario, AMANHA, time(17, 30), 30, AGORA) is None

def test_regras_horario_termina_no_inicio_do_intervalo(cenario):
    # Um serviço de 30 min às 11:30 termina exatamente no início do almoço
    _, horario, _ = cenario
    assert verificar_regras_horario(horario, AMANHA, time(11, 30), 30, AGORA) is None

def test_regras_horario_data_passada(cenario):
    _, horario, _ = cenario
    ontem = HOJE - timedelta(days=1)
    assert "passado" in verificar_regras_horario(horario, ontem, time(9, 0), 30, AGORA)

def test_regras_horario_limite_30_dias(cenario):
    _, horario, _ = cenario
    limite = HOJE + timedelta(days=30)
    depois_do_limite = HOJE + timedelta(days=31)
    assert verificar_regras_horario(horario, limite, time(9, 0), 30, AGORA) is None
    assert "30 dias" in verificar_regras_horario(
        horario, depois_do_limite, time(9, 0), 30, AGORA
    )

def test_regras_horario_dia_sem_funcionamento(sessao_teste):
    # Fecha o estabelecimento no dia da semana de amanhã
    estabelecimento = criar_estabelecimento(sessao_teste)
    dia_fechado = DIAS_SEMANA[AMANHA.weekday()]
    horario = criar_horario(sessao_teste, estabelecimento, **{dia_fechado: False})
    motivo = verificar_regras_horario(horario, AMANHA, time(9, 0), 30, AGORA)
    assert motivo == "O estabelecimento não funciona neste dia."

def test_regras_horario_hoje_ja_passou(cenario):
    # Agora são 10:00 de hoje
    _, horario, _ = cenario
    agora = datetime.combine(HOJE, time(10, 0))
    assert verificar_regras_horario(horario, HOJE, time(9, 50), 30, agora) == "Este horário já passou."
    assert verificar_regras_horario(horario, HOJE, time(10, 0), 30, agora) == "Este horário já passou."
    assert verificar_regras_horario(horario, HOJE, time(10, 10), 30, agora) is None

def test_regras_horario_nao_configurado():
    motivo = verificar_regras_horario(None, AMANHA, time(9, 0), 30, AGORA)
    assert "não configurou" in motivo


# ---------- Disponibilidade

def test_disponibilidade_sem_agendamentos(sessao_teste, cenario):
    _, _, servico = cenario
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    # 09:00 a 11:30 (antes do almoço) e 13:00 a 17:30, de 10 em 10 minutos
    assert horarios[0] == time(9, 0)
    assert horarios[1] == time(9, 10)
    assert time(11, 30) in horarios
    assert time(11, 40) not in horarios
    assert time(12, 30) not in horarios
    assert time(13, 0) in horarios
    assert horarios[-1] == time(17, 30)
    assert len(horarios) == 16 + 28

def test_disponibilidade_considera_agendamentos(sessao_teste, cenario):
    # Agenda 10:00 às 10:30
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    # 09:30 terminaria às 10:00 (livre), 09:40 até 10:20 conflitam, 10:30 livre
    assert time(9, 30) in horarios
    for ocupado in (time(9, 40), time(9, 50), time(10, 0), time(10, 10), time(10, 20)):
        assert ocupado not in horarios
    assert time(10, 30) in horarios

def test_disponibilidade_ignora_cancelados(sessao_teste, cenario):
    # Agenda e cancela 10:00
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    cancelar_agendamento(
        agendamento.id_agendamento, estabelecimento.id_estabelecimento, sessao_teste
    )
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    # O horário volta a ficar disponível
    assert time(10, 0) in horarios

def test_disponibilidade_agenda_unica_entre_servicos(sessao_teste, cenario):
    # Agenda um serviço de 60 min às 14:00
    estabelecimento, _, servico = cenario
    servico_longo = criar_servico(sessao_teste, estabelecimento, duracao=60, nome="Coloração")
    agendar(sessao_teste, estabelecimento, servico_longo, time(14, 0))
    # Consulta o outro serviço
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    # O estabelecimento tem uma única agenda, então 14:00 a 14:50 ficam ocupados
    assert time(14, 30) not in horarios
    assert time(15, 0) in horarios

def test_disponibilidade_hoje_so_horarios_futuros(sessao_teste, cenario):
    _, _, servico = cenario
    agora = datetime.combine(HOJE, time(15, 5))
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, HOJE, sessao_teste, agora=agora
    )
    assert horarios[0] == time(15, 10)

def test_disponibilidade_abertura_fora_da_grade(sessao_teste):
    # Abre 09:05: os horários seguem a grade de 10 minutos (09:10, 09:20...)
    estabelecimento = criar_estabelecimento(sessao_teste)
    criar_horario(sessao_teste, estabelecimento, hora_abertura=time(9, 5))
    servico = criar_servico(sessao_teste, estabelecimento)
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    assert horarios[0] == time(9, 10)

def test_disponibilidade_sem_horario_configurado(sessao_teste):
    estabelecimento = criar_estabelecimento(sessao_teste)
    servico = criar_servico(sessao_teste, estabelecimento)
    _, horarios = consultar_disponibilidade(
        "barbearia-joao", servico.id_servico, AMANHA, sessao_teste, agora=AGORA
    )
    assert horarios == []

def test_disponibilidade_servico_inativo(sessao_teste, cenario):
    estabelecimento, _, _ = cenario
    inativo = criar_servico(sessao_teste, estabelecimento, ativo=False)
    with pytest.raises(ServicoNaoEncontradoError):
        consultar_disponibilidade(
            "barbearia-joao", inativo.id_servico, AMANHA, sessao_teste, agora=AGORA
        )

def test_disponibilidade_servico_de_outro_estabelecimento(sessao_teste, cenario):
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    servico_outro = criar_servico(sessao_teste, outro)
    with pytest.raises(ServicoNaoEncontradoError):
        consultar_disponibilidade(
            "barbearia-joao", servico_outro.id_servico, AMANHA, sessao_teste, agora=AGORA
        )

def test_disponibilidade_estabelecimento_inexistente(sessao_teste):
    with pytest.raises(EstabelecimentoNaoEncontradoError):
        consultar_disponibilidade("inexistente", 1, AMANHA, sessao_teste, agora=AGORA)


# ---------- Cadastro

def test_cadastrar_agendamento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico, time(9, 0))
    assert agendamento.id_agendamento > 0
    assert agendamento.horario_fim == time(9, 30)
    assert agendamento.status == "agendado"
    assert agendamento.data_cancelamento is None
    assert agendamento.data_cadastro == AGORA

def test_cadastrar_agendamento_conflito(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    # 10:20 começaria antes de 10:30, quando o primeiro termina
    with pytest.raises(HorarioIndisponivelError):
        agendar(sessao_teste, estabelecimento, servico, time(10, 20))

def test_cadastrar_agendamento_encostado(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    # Começa exatamente quando o anterior termina
    agendamento = agendar(sessao_teste, estabelecimento, servico, time(10, 30))
    assert agendamento.horario_fim == time(11, 0)

def test_cadastrar_agendamento_mesmo_horario_outro_dia(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    depois_de_amanha = AMANHA + timedelta(days=1)
    agendamento = agendar(sessao_teste, estabelecimento, servico, time(10, 0), depois_de_amanha)
    assert agendamento.data_agendamento == depois_de_amanha

def test_cadastrar_agendamento_mesmo_horario_outro_estabelecimento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico, time(10, 0))
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    criar_horario(sessao_teste, outro)
    servico_outro = criar_servico(sessao_teste, outro)
    # Agendas de estabelecimentos diferentes não conflitam
    agendamento = agendar(sessao_teste, outro, servico_outro, time(10, 0))
    assert agendamento.id_agendamento > 0

def test_cadastrar_agendamento_horario_invalido(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    with pytest.raises(AgendamentoInvalidoError, match="intervalo do estabelecimento"):
        agendar(sessao_teste, estabelecimento, servico, time(12, 0))

def test_cadastrar_agendamento_servico_inativo(sessao_teste, cenario):
    estabelecimento, _, _ = cenario
    inativo = criar_servico(sessao_teste, estabelecimento, ativo=False)
    with pytest.raises(ServicoNaoEncontradoError):
        agendar(sessao_teste, estabelecimento, inativo)

def test_cadastrar_agendamento_publico(sessao_teste, cenario):
    _, _, servico = cenario
    agendamento = cadastrar_agendamento_publico(
        "barbearia-joao", criar_dados(servico), sessao_teste, agora=AGORA
    )
    assert agendamento.id_servico == servico.id_servico

def test_cadastrar_agendamento_publico_servico_de_outro_estabelecimento(sessao_teste, cenario):
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    servico_outro = criar_servico(sessao_teste, outro)
    # Não pode agendar serviço de outro estabelecimento pela página deste
    with pytest.raises(ServicoNaoEncontradoError):
        cadastrar_agendamento_publico(
            "barbearia-joao", criar_dados(servico_outro), sessao_teste, agora=AGORA
        )


# ---------- Consulta e listagem

def test_listar_agendamentos_ordenados_e_filtrados(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    depois_de_amanha = AMANHA + timedelta(days=1)
    tarde = agendar(sessao_teste, estabelecimento, servico, time(15, 0))
    manha = agendar(sessao_teste, estabelecimento, servico, time(9, 0))
    outro_dia = agendar(sessao_teste, estabelecimento, servico, time(9, 0), depois_de_amanha)
    cancelar_agendamento(
        outro_dia.id_agendamento, estabelecimento.id_estabelecimento, sessao_teste
    )
    id_estab = estabelecimento.id_estabelecimento
    # Ordenados por data e horário
    todos = listar_agendamentos(id_estab, sessao_teste)
    assert [a.id_agendamento for a in todos] == [
        manha.id_agendamento,
        tarde.id_agendamento,
        outro_dia.id_agendamento,
    ]
    # Filtro por data e por status
    assert len(listar_agendamentos(id_estab, sessao_teste, data_agendamento=AMANHA)) == 2
    cancelados = listar_agendamentos(id_estab, sessao_teste, status="cancelado")
    assert [a.id_agendamento for a in cancelados] == [outro_dia.id_agendamento]

def test_listar_agendamentos_apenas_do_estabelecimento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendar(sessao_teste, estabelecimento, servico)
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    assert listar_agendamentos(outro.id_estabelecimento, sessao_teste) == []

def test_obter_agendamento_de_outro_estabelecimento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico)
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    with pytest.raises(AgendamentoNaoEncontradoError):
        obter_agendamento(agendamento.id_agendamento, outro.id_estabelecimento, sessao_teste)

def test_obter_agendamento_inexistente(sessao_teste, cenario):
    estabelecimento, _, _ = cenario
    with pytest.raises(AgendamentoNaoEncontradoError):
        obter_agendamento(999, estabelecimento.id_estabelecimento, sessao_teste)


# ---------- Cancelamento

def test_cancelar_agendamento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico)
    momento = datetime.combine(HOJE, time(8, 30))
    resultado = cancelar_agendamento(
        agendamento.id_agendamento,
        estabelecimento.id_estabelecimento,
        sessao_teste,
        agora=momento,
    )
    assert resultado.status == "cancelado"
    assert resultado.data_cancelamento == momento

def test_cancelar_agendamento_ja_cancelado(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico)
    cancelar_agendamento(
        agendamento.id_agendamento, estabelecimento.id_estabelecimento, sessao_teste
    )
    with pytest.raises(AgendamentoCanceladoError):
        cancelar_agendamento(
            agendamento.id_agendamento, estabelecimento.id_estabelecimento, sessao_teste
        )

def test_cancelar_agendamento_de_outro_estabelecimento(sessao_teste, cenario):
    estabelecimento, _, servico = cenario
    agendamento = agendar(sessao_teste, estabelecimento, servico)
    outro = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    with pytest.raises(AgendamentoNaoEncontradoError):
        cancelar_agendamento(agendamento.id_agendamento, outro.id_estabelecimento, sessao_teste)
