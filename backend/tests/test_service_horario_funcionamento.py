from datetime import time

import pytest

from app.models.estabelecimento import Estabelecimento
from app.schemas.horario_funcionamento import (
    HorarioFuncionamentoAtualizacao,
    HorarioFuncionamentoCriacao,
)
from app.services.horario_funcionamento import (
    HorarioInvalidoError,
    HorarioNaoConfiguradoError,
    atualizar_horario,
    buscar_horario,
    definir_horario,
    obter_horario,
)


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
    # Adiciona e salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

# Cria dados de horário: segunda a sexta, 09:00 às 18:00, almoço 12:00 às 13:00
def criar_dados_horario(**alteracoes):
    dados = {
        "segunda": True,
        "terca": True,
        "quarta": True,
        "quinta": True,
        "sexta": True,
        "hora_abertura": time(9, 0),
        "hora_fechamento": time(18, 0),
        "inicio_intervalo": time(12, 0),
        "fim_intervalo": time(13, 0),
    }
    dados.update(alteracoes)
    return HorarioFuncionamentoCriacao(**dados)

def test_definir_horario_cria(sessao_teste):
    # Cria estabelecimento sem horário
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Define o horário usando o Service
    horario = definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert horario.id_horario > 0
    assert horario.id_estabelecimento == estabelecimento.id_estabelecimento
    assert horario.segunda is True
    assert horario.sabado is False
    assert horario.hora_abertura == time(9, 0)
    assert horario.fim_intervalo == time(13, 0)

def test_definir_horario_substitui(sessao_teste):
    # Cria estabelecimento e define um horário
    estabelecimento = criar_estabelecimento(sessao_teste)
    primeiro = definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Define novamente, agora só sábado e sem intervalo
    segundo = definir_horario(
        HorarioFuncionamentoCriacao(  # pyright: ignore[reportCallIssue]
            sabado=True,
            hora_abertura=time(8, 0),
            hora_fechamento=time(12, 0),
        ),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    # Continua sendo o mesmo registro (1 pra 1), com todos os campos substituídos
    assert segundo.id_horario == primeiro.id_horario
    assert segundo.segunda is False
    assert segundo.sabado is True
    assert segundo.inicio_intervalo is None
    assert segundo.fim_intervalo is None

def test_obter_horario_nao_configurado(sessao_teste):
    # Cria estabelecimento sem horário
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Resultado esperado e comparações
    assert buscar_horario(estabelecimento.id_estabelecimento, sessao_teste) is None
    with pytest.raises(HorarioNaoConfiguradoError):
        obter_horario(estabelecimento.id_estabelecimento, sessao_teste)

def test_obter_horario_apenas_do_estabelecimento(sessao_teste):
    # Cria dois estabelecimentos e horário só para o primeiro
    estabelecimento = criar_estabelecimento(sessao_teste)
    outro_estabelecimento = criar_estabelecimento(
        sessao_teste,
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    with pytest.raises(HorarioNaoConfiguradoError):
        obter_horario(outro_estabelecimento.id_estabelecimento, sessao_teste)

def test_atualizar_horario(sessao_teste):
    # Cria estabelecimento e define horário
    estabelecimento = criar_estabelecimento(sessao_teste)
    definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Atualiza apenas o fechamento e abre no sábado
    horario = atualizar_horario(
        HorarioFuncionamentoAtualizacao(  # pyright: ignore[reportCallIssue]
            hora_fechamento=time(20, 0),
            sabado=True,
        ),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    # Os campos não informados permanecem iguais
    assert horario.hora_fechamento == time(20, 0)
    assert horario.sabado is True
    assert horario.hora_abertura == time(9, 0)
    assert horario.inicio_intervalo == time(12, 0)

def test_atualizar_horario_remover_intervalo(sessao_teste):
    # Cria estabelecimento e define horário com intervalo
    estabelecimento = criar_estabelecimento(sessao_teste)
    definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Remove o intervalo
    horario = atualizar_horario(
        HorarioFuncionamentoAtualizacao(  # pyright: ignore[reportCallIssue]
            inicio_intervalo=None,
            fim_intervalo=None,
        ),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert horario.inicio_intervalo is None
    assert horario.fim_intervalo is None

def test_atualizar_horario_abertura_depois_do_fechamento_atual(sessao_teste):
    # Cria estabelecimento e define horário até 18:00
    estabelecimento = criar_estabelecimento(sessao_teste)
    definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Tenta mudar só a abertura para depois do fechamento atual
    # O schema de atualização sozinho não percebe, o Service valida o resultado
    with pytest.raises(HorarioInvalidoError, match="abertura"):
        atualizar_horario(
            HorarioFuncionamentoAtualizacao(hora_abertura=time(19, 0)),  # pyright: ignore[reportCallIssue]
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_horario_intervalo_fora_do_funcionamento(sessao_teste):
    # Cria estabelecimento e define horário com almoço 12:00 às 13:00
    estabelecimento = criar_estabelecimento(sessao_teste)
    definir_horario(
        criar_dados_horario(),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Tenta fechar antes do fim do intervalo atual
    with pytest.raises(HorarioInvalidoError, match="intervalo"):
        atualizar_horario(
            HorarioFuncionamentoAtualizacao(hora_fechamento=time(12, 30)),  # pyright: ignore[reportCallIssue]
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_horario_sem_dias(sessao_teste):
    # Cria estabelecimento e define horário só na segunda
    estabelecimento = criar_estabelecimento(sessao_teste)
    definir_horario(
        HorarioFuncionamentoCriacao(  # pyright: ignore[reportCallIssue]
            segunda=True,
            hora_abertura=time(9, 0),
            hora_fechamento=time(18, 0),
        ),
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Tenta desmarcar o único dia de funcionamento
    with pytest.raises(HorarioInvalidoError, match="dia"):
        atualizar_horario(
            HorarioFuncionamentoAtualizacao(segunda=False),  # pyright: ignore[reportCallIssue]
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_horario_nao_configurado(sessao_teste):
    # Cria estabelecimento sem horário
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Tenta atualizar
    with pytest.raises(HorarioNaoConfiguradoError):
        atualizar_horario(
            HorarioFuncionamentoAtualizacao(sabado=True),  # pyright: ignore[reportCallIssue]
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )
