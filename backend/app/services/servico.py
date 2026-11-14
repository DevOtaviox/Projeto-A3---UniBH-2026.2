from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.servico import Servico
from app.schemas.servico import ServicoAtualizacao, ServicoCriacao


# Exceção para serviço que não existe ou pertence a outro estabelecimento
class ServicoNaoEncontradoError(Exception):
    pass

# Todas as funções recebem o id_estabelecimento
# Assim um estabelecimento só consegue acessar os próprios serviços

def cadastrar_servico(
    dados: ServicoCriacao,
    id_estabelecimento: int,
    sessao: Session,
) -> Servico:
    # Cria objeto serviço vinculado ao estabelecimento
    servico = Servico(
        id_estabelecimento=id_estabelecimento,
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        duracao_minutos=dados.duracao_minutos,
    )
    # Salva no db
    sessao.add(servico)
    sessao.commit()
    # Atualiza os dados do objeto depois de criado no db, incluindo a pk
    sessao.refresh(servico)
    return servico

def listar_servicos(
    id_estabelecimento: int,
    sessao: Session,
) -> list[Servico]:
    # Consulta apenas os serviços do estabelecimento, ativos e inativos
    consulta = (
        select(Servico)
        .where(Servico.id_estabelecimento == id_estabelecimento)
        .order_by(Servico.id_servico)
    )
    return list(sessao.scalars(consulta))

def obter_servico(
    id_servico: int,
    id_estabelecimento: int,
    sessao: Session,
) -> Servico:
    # Consulta o serviço pelo id, filtrando pelo estabelecimento
    consulta = select(Servico).where(
        Servico.id_servico == id_servico,
        Servico.id_estabelecimento == id_estabelecimento,
    )
    servico = sessao.scalar(consulta)
    # Levanta erro pra serviço inexistente ou de outro estabelecimento
    # O erro é o mesmo nos dois casos pra não revelar serviços de terceiros
    if servico is None:
        raise ServicoNaoEncontradoError("Serviço não encontrado.")
    return servico

# Também é usada para inativar e reativar o serviço com o campo ativo
# O serviço não é excluído pra manter o histórico de agendamentos
def atualizar_servico(
    id_servico: int,
    dados: ServicoAtualizacao,
    id_estabelecimento: int,
    sessao: Session,
) -> Servico:
    # Consulta o serviço do estabelecimento
    servico = obter_servico(id_servico, id_estabelecimento, sessao)
    # Altera apenas os campos informados na requisição
    # exclude_unset=True exclui os campos não informados
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(servico, campo, valor)
    # Salva no db
    sessao.commit()
    sessao.refresh(servico)
    return servico
