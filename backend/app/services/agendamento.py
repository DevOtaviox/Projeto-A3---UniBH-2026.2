from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agendamento import Agendamento
from app.models.horario_funcionamento import HorarioFuncionamento
from app.models.servico import Servico
from app.schemas.agendamento import (
    INTERVALO_MINUTOS,
    LIMITE_DIAS_AGENDAMENTO,
    AgendamentoCriacao,
)
from app.services.estabelecimento import buscar_estabelecimento_publico
from app.services.horario_funcionamento import buscar_horario
from app.services.servico import ServicoNaoEncontradoError

# Regras de negócio do agendamento (levantamento de requisitos)
# LIMITE_DIAS_AGENDAMENTO (30 dias) e INTERVALO_MINUTOS (10 min) vêm do schema
# Assim o schema e o service usam sempre os mesmos valores
# Ordem igual à de date.weekday(): segunda = 0 ... domingo = 6
DIAS_SEMANA = (
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
)


# Exceção para agendamento que não existe ou pertence a outro estabelecimento
class AgendamentoNaoEncontradoError(Exception):
    pass

# Exceção para horário que não respeita as regras do estabelecimento
# Ex.: dia sem funcionamento, fora do horário, no intervalo, data além de 30 dias
class AgendamentoInvalidoError(Exception):
    pass

# Exceção para horário que conflita com outro agendamento
class HorarioIndisponivelError(Exception):
    pass

# Exceção para cancelar um agendamento já cancelado
class AgendamentoCanceladoError(Exception):
    pass


# Converte um horário em minutos desde a meia-noite (09:30 -> 570)
def _para_minutos(horario: time) -> int:
    return horario.hour * 60 + horario.minute

# Converte minutos desde a meia-noite em horário (570 -> 09:30)
def _para_horario(minutos: int) -> time:
    return time(minutos // 60, minutos % 60)

# Verifica se dois períodos [inicio, fim) se sobrepõem
# Um atendimento que termina às 10:00 não conflita com outro que começa às 10:00
def _periodos_sobrepostos(
    inicio_a: int,
    fim_a: int,
    inicio_b: int,
    fim_b: int,
) -> bool:
    return inicio_a < fim_b and inicio_b < fim_a

# Retorna o motivo pelo qual o período não pode ser agendado
# Retorna None se o período respeitar as regras do estabelecimento
# Não verifica conflito com outros agendamentos (isso é feito separadamente)
def verificar_regras_horario(
    horario: HorarioFuncionamento | None,
    data_agendamento: date,
    horario_inicio: time,
    duracao_minutos: int,
    agora: datetime,
) -> str | None:
    hoje = agora.date()
    # Valida a data dentro da janela de agendamento
    if data_agendamento < hoje:
        return "A data do agendamento não pode estar no passado."
    if data_agendamento > hoje + timedelta(days=LIMITE_DIAS_AGENDAMENTO):
        return (
            "Agendamentos só podem ser feitos com até "
            f"{LIMITE_DIAS_AGENDAMENTO} dias de antecedência."
        )
    # Valida se o estabelecimento configurou o horário de funcionamento
    if horario is None:
        return "O estabelecimento ainda não configurou o horário de funcionamento."
    # Valida se o estabelecimento funciona no dia da semana escolhido
    if not getattr(horario, DIAS_SEMANA[data_agendamento.weekday()]):
        return "O estabelecimento não funciona neste dia."
    # Valida horário sem segundos (ex.: 09:30:15 não é aceito)
    if horario_inicio.second or horario_inicio.microsecond:
        return "Informe o horário apenas com horas e minutos."
    inicio = _para_minutos(horario_inicio)
    fim = inicio + duracao_minutos
    abertura = _para_minutos(horario.hora_abertura)
    fechamento = _para_minutos(horario.hora_fechamento)
    # Valida se o atendimento inteiro cabe no horário de funcionamento
    if inicio < abertura or fim > fechamento:
        return "O horário está fora do funcionamento do estabelecimento."
    # Valida se o horário segue os intervalos de 10 minutos (10:00, 10:10...)
    # Mesma regra do schema, repetida aqui porque a disponibilidade não passa por ele
    if inicio % INTERVALO_MINUTOS != 0:
        return f"O horário deve seguir intervalos de {INTERVALO_MINUTOS} minutos."
    # Valida se o atendimento não invade o intervalo (almoço)
    if (
        horario.inicio_intervalo is not None
        and horario.fim_intervalo is not None
        and _periodos_sobrepostos(
            inicio,
            fim,
            _para_minutos(horario.inicio_intervalo),
            _para_minutos(horario.fim_intervalo),
        )
    ):
        return "O horário coincide com o intervalo do estabelecimento."
    # Valida se o horário de hoje ainda não passou
    if data_agendamento == hoje and horario_inicio <= agora.time():
        return "Este horário já passou."
    return None

# Calcula os horários de início disponíveis para um serviço em uma data
# ocupados: períodos (inicio, fim) em minutos dos agendamentos ativos do dia
def calcular_horarios_disponiveis(
    horario: HorarioFuncionamento | None,
    data_agendamento: date,
    duracao_minutos: int,
    ocupados: list[tuple[int, int]],
    agora: datetime,
) -> list[time]:
    if horario is None:
        return []
    disponiveis = []
    abertura = _para_minutos(horario.hora_abertura)
    fechamento = _para_minutos(horario.hora_fechamento)
    # Primeiro horário múltiplo de 10 minutos a partir da abertura
    # Ex.: abertura 09:05 -> primeiro horário 09:10
    primeiro_inicio = -(-abertura // INTERVALO_MINUTOS) * INTERVALO_MINUTOS
    # Percorre os horários de 10 em 10 minutos enquanto o serviço couber no dia
    for inicio in range(
        primeiro_inicio,
        fechamento - duracao_minutos + 1,
        INTERVALO_MINUTOS,
    ):
        fim = inicio + duracao_minutos
        # Ignora horários que não respeitam as regras do estabelecimento
        if verificar_regras_horario(
            horario,
            data_agendamento,
            _para_horario(inicio),
            duracao_minutos,
            agora,
        ) is not None:
            continue
        # Ignora horários que conflitam com agendamentos existentes
        if any(
            _periodos_sobrepostos(inicio, fim, inicio_ocupado, fim_ocupado)
            for inicio_ocupado, fim_ocupado in ocupados
        ):
            continue
        disponiveis.append(_para_horario(inicio))
    return disponiveis

# Consulta o serviço filtrando pelo estabelecimento
# exigir_ativo=True impede agendar em serviços inativos
def _obter_servico_do_estabelecimento(
    id_servico: int,
    id_estabelecimento: int,
    sessao: Session,
    exigir_ativo: bool = True,
) -> Servico:
    consulta = select(Servico).where(
        Servico.id_servico == id_servico,
        Servico.id_estabelecimento == id_estabelecimento,
    )
    servico = sessao.scalar(consulta)
    # O erro é o mesmo nos dois casos pra não revelar serviços de terceiros
    if servico is None or (exigir_ativo and not servico.ativo):
        raise ServicoNaoEncontradoError("Serviço não encontrado.")
    return servico

# Lista os períodos ocupados (em minutos) de um estabelecimento em uma data
# Considera apenas agendamentos ativos: cancelados liberam o horário
# O estabelecimento tem uma única agenda, então todos os serviços contam
def _listar_periodos_ocupados(
    id_estabelecimento: int,
    data_agendamento: date,
    sessao: Session,
) -> list[tuple[int, int]]:
    consulta = (
        select(Agendamento.horario_inicio, Agendamento.horario_fim)
        .join(Servico)
        .where(
            Servico.id_estabelecimento == id_estabelecimento,
            Agendamento.data_agendamento == data_agendamento,
            Agendamento.status == "agendado",
        )
    )
    return [
        (_para_minutos(inicio), _para_minutos(fim))
        for inicio, fim in sessao.execute(consulta)
    ]

# Valida o período escolhido e retorna o horário de término calculado
def _validar_periodo(
    id_estabelecimento: int,
    servico: Servico,
    data_agendamento: date,
    horario_inicio: time,
    sessao: Session,
    agora: datetime,
) -> time:
    horario = buscar_horario(id_estabelecimento, sessao)
    # Valida as regras do estabelecimento
    motivo = verificar_regras_horario(
        horario,
        data_agendamento,
        horario_inicio,
        servico.duracao_minutos,
        agora,
    )
    if motivo is not None:
        raise AgendamentoInvalidoError(motivo)
    # Valida conflito com os agendamentos existentes
    inicio = _para_minutos(horario_inicio)
    fim = inicio + servico.duracao_minutos
    ocupados = _listar_periodos_ocupados(
        id_estabelecimento,
        data_agendamento,
        sessao,
    )
    if any(
        _periodos_sobrepostos(inicio, fim, inicio_ocupado, fim_ocupado)
        for inicio_ocupado, fim_ocupado in ocupados
    ):
        raise HorarioIndisponivelError(
            "Este horário não está mais disponível. Escolha outro horário."
        )
    return _para_horario(fim)


# Consulta pública dos horários disponíveis de um serviço em uma data
def consultar_disponibilidade(
    identificador: str,
    id_servico: int,
    data_agendamento: date,
    sessao: Session,
    agora: datetime | None = None,
) -> tuple[Servico, list[time]]:
    agora = agora or datetime.now()
    # Busca estabelecimento ativo e serviço ativo dele
    estabelecimento = buscar_estabelecimento_publico(identificador, sessao)
    servico = _obter_servico_do_estabelecimento(
        id_servico,
        estabelecimento.id_estabelecimento,
        sessao,
    )
    horario = buscar_horario(estabelecimento.id_estabelecimento, sessao)
    ocupados = _listar_periodos_ocupados(
        estabelecimento.id_estabelecimento,
        data_agendamento,
        sessao,
    )
    horarios = calcular_horarios_disponiveis(
        horario,
        data_agendamento,
        servico.duracao_minutos,
        ocupados,
        agora,
    )
    return servico, horarios

# Cadastro de agendamento
# Usado pelo cliente (página pública) e pelo proprietário (área administrativa)
def cadastrar_agendamento(
    dados: AgendamentoCriacao,
    id_estabelecimento: int,
    sessao: Session,
    agora: datetime | None = None,
) -> Agendamento:
    agora = agora or datetime.now()
    servico = _obter_servico_do_estabelecimento(
        dados.id_servico,
        id_estabelecimento,
        sessao,
    )
    # Valida o horário logo antes de salvar e calcula o término
    horario_fim = _validar_periodo(
        id_estabelecimento,
        servico,
        dados.data_agendamento,
        dados.horario_inicio,
        sessao,
        agora,
    )
    # Cria objeto agendamento, todo agendamento novo começa como "agendado"
    agendamento = Agendamento(
        id_servico=servico.id_servico,
        nome_cliente=dados.nome_cliente,
        telefone_cliente=dados.telefone_cliente,
        data_agendamento=dados.data_agendamento,
        horario_inicio=dados.horario_inicio,
        horario_fim=horario_fim,
        status="agendado",
        data_cadastro=agora,
    )
    # Salva no db
    sessao.add(agendamento)
    sessao.commit()
    sessao.refresh(agendamento)
    return agendamento

# Cadastro de agendamento pela página pública do estabelecimento
def cadastrar_agendamento_publico(
    identificador: str,
    dados: AgendamentoCriacao,
    sessao: Session,
    agora: datetime | None = None,
) -> Agendamento:
    estabelecimento = buscar_estabelecimento_publico(identificador, sessao)
    return cadastrar_agendamento(
        dados,
        estabelecimento.id_estabelecimento,
        sessao,
        agora,
    )

# Listagem dos agendamentos do estabelecimento, com filtros opcionais
def listar_agendamentos(
    id_estabelecimento: int,
    sessao: Session,
    data_agendamento: date | None = None,
    status: str | None = None,
) -> list[Agendamento]:
    consulta = (
        select(Agendamento)
        .join(Servico)
        .where(Servico.id_estabelecimento == id_estabelecimento)
        .order_by(
            Agendamento.data_agendamento,
            Agendamento.horario_inicio,
            Agendamento.id_agendamento,
        )
    )
    if data_agendamento is not None:
        consulta = consulta.where(
            Agendamento.data_agendamento == data_agendamento
        )
    if status is not None:
        consulta = consulta.where(Agendamento.status == status)
    return list(sessao.scalars(consulta))

# Consulta de um agendamento do estabelecimento
def obter_agendamento(
    id_agendamento: int,
    id_estabelecimento: int,
    sessao: Session,
) -> Agendamento:
    consulta = (
        select(Agendamento)
        .join(Servico)
        .where(
            Agendamento.id_agendamento == id_agendamento,
            Servico.id_estabelecimento == id_estabelecimento,
        )
    )
    agendamento = sessao.scalar(consulta)
    # O erro é o mesmo nos dois casos pra não revelar agendamentos de terceiros
    if agendamento is None:
        raise AgendamentoNaoEncontradoError("Agendamento não encontrado.")
    return agendamento

# Cancelamento de agendamento pelo proprietário (RF20 e RF21)
# É a única alteração permitida em um agendamento
# O registro não é excluído: o status muda e o horário volta a ficar livre
def cancelar_agendamento(
    id_agendamento: int,
    id_estabelecimento: int,
    sessao: Session,
    agora: datetime | None = None,
) -> Agendamento:
    agendamento = obter_agendamento(id_agendamento, id_estabelecimento, sessao)
    if agendamento.status == "cancelado":
        raise AgendamentoCanceladoError("Este agendamento já está cancelado.")
    agendamento.status = "cancelado"
    agendamento.data_cancelamento = agora or datetime.now()
    # Salva no db
    sessao.commit()
    sessao.refresh(agendamento)
    return agendamento
