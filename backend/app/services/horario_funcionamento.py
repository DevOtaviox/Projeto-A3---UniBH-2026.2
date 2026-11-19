from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.horario_funcionamento import HorarioFuncionamento
from app.schemas.horario_funcionamento import (
    HorarioFuncionamentoAtualizacao,
    HorarioFuncionamentoCriacao,
)
from app.services.estabelecimento import buscar_estabelecimento_publico


# Exceção para estabelecimento que ainda não configurou o horário
class HorarioNaoConfiguradoError(Exception):
    pass

# Exceção para horário que fica inválido depois de juntar com os dados atuais
class HorarioInvalidoError(Exception):
    pass

# Campos do horário que podem ser configurados pelo proprietário
CAMPOS_HORARIO = tuple(HorarioFuncionamentoCriacao.model_fields)

# Cada estabelecimento tem no máximo um horário de funcionamento (relação 1 pra 1)
# Todas as funções recebem o id_estabelecimento do token
# Assim um estabelecimento só acessa o próprio horário

def buscar_horario(
    id_estabelecimento: int,
    sessao: Session,
) -> HorarioFuncionamento | None:
    # Consulta o horário do estabelecimento, retorna None se não existir
    consulta = select(HorarioFuncionamento).where(
        HorarioFuncionamento.id_estabelecimento == id_estabelecimento
    )
    return sessao.scalar(consulta)

def obter_horario(
    id_estabelecimento: int,
    sessao: Session,
) -> HorarioFuncionamento:
    # Consulta o horário e levanta erro se ainda não foi configurado
    horario = buscar_horario(id_estabelecimento, sessao)
    if horario is None:
        raise HorarioNaoConfiguradoError(
            "Horário de funcionamento não configurado."
        )
    return horario

# Consulta pública do horário pelo identificador do estabelecimento
# Usada pela página do cliente, sem autenticação
# Estabelecimento inativo ou inexistente levanta EstabelecimentoNaoEncontradoError
def obter_horario_publico(
    identificador: str,
    sessao: Session,
) -> HorarioFuncionamento:
    estabelecimento = buscar_estabelecimento_publico(identificador, sessao)
    return obter_horario(estabelecimento.id_estabelecimento, sessao)

# Cria ou substitui o horário de funcionamento inteiro (PUT)
def definir_horario(
    dados: HorarioFuncionamentoCriacao,
    id_estabelecimento: int,
    sessao: Session,
) -> HorarioFuncionamento:
    horario = buscar_horario(id_estabelecimento, sessao)
    # Cria o horário se o estabelecimento ainda não tiver um
    if horario is None:
        horario = HorarioFuncionamento(id_estabelecimento=id_estabelecimento)
        sessao.add(horario)
    # Substitui todos os campos, inclusive o intervalo (pode virar None)
    for campo, valor in dados.model_dump().items():
        setattr(horario, campo, valor)
    # Salva no db
    sessao.commit()
    sessao.refresh(horario)
    return horario

# Altera apenas os campos informados (PATCH)
def atualizar_horario(
    dados: HorarioFuncionamentoAtualizacao,
    id_estabelecimento: int,
    sessao: Session,
) -> HorarioFuncionamento:
    horario = obter_horario(id_estabelecimento, sessao)
    # Junta os dados atuais com os campos informados
    dados_atuais = {campo: getattr(horario, campo) for campo in CAMPOS_HORARIO}
    dados_atuais.update(dados.model_dump(exclude_unset=True))
    # Valida o resultado com as mesmas regras do cadastro
    # Ex.: abertura nova depois do fechamento atual, intervalo fora do horário
    try:
        horario_validado = HorarioFuncionamentoCriacao(**dados_atuais)
    except ValidationError as erro:
        mensagens = "; ".join(
            detalhe["msg"].removeprefix("Value error, ")
            for detalhe in erro.errors()
        )
        raise HorarioInvalidoError(mensagens) from erro
    # Aplica os dados validados
    for campo, valor in horario_validado.model_dump().items():
        setattr(horario, campo, valor)
    # Salva no db
    sessao.commit()
    sessao.refresh(horario)
    return horario
