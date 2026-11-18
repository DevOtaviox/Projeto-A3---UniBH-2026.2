from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoAtualizacao,
    EstabelecimentoCriacao,
)


# Exceção para informações duplicadas
class EstabelecimentoDuplicadoError(Exception):
    pass

# Exceção para estabelecimento não encontrado
class EstabelecimentoNaoEncontradoError(Exception):
    pass

def cadastrar_estabelecimento(
    dados: EstabelecimentoCriacao,
    sessao: Session,
) -> Estabelecimento:
    # Verifica e-mail duplicado
    consulta_email = select(Estabelecimento.id_estabelecimento).where(
        Estabelecimento.email == dados.email
    )
    if sessao.scalar(consulta_email) is not None:
        raise EstabelecimentoDuplicadoError("E-mail já cadastrado.")
    # Verifica se o documento já está cadastrado
    consulta_documento = select(Estabelecimento.id_estabelecimento).where(
        Estabelecimento.documento == dados.documento
    )
    if sessao.scalar(consulta_documento) is not None:
        raise EstabelecimentoDuplicadoError("Documento já cadastrado.")
    # Verifica identificador duplicado
    consulta_identificador = select(Estabelecimento.id_estabelecimento).where(
        Estabelecimento.identificador == dados.identificador
    )
    if sessao.scalar(consulta_identificador) is not None:
        raise EstabelecimentoDuplicadoError("Identificador já cadastrado.")
    # Cria objeto estabelecimento
    estabelecimento = Estabelecimento(
        nome=dados.nome,
        endereco=dados.endereco,
        imagem=dados.imagem,
        tipo_documento=dados.tipo_documento,
        documento=dados.documento,
        identificador=dados.identificador,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
    )
    # Salva no db
    try:
        sessao.add(estabelecimento)
        sessao.commit()
    # Levanta e retorna erro se houver algum dos dados duplicados
    except IntegrityError as erro:
        sessao.rollback()
        raise EstabelecimentoDuplicadoError(
            "E-mail, documento ou identificador já cadastrado."
        ) from erro
    # Atualiza os dados do objeto depois de criado no db, incluindo a pk
    sessao.refresh(estabelecimento)
    return estabelecimento

def buscar_estabelecimento_publico(
    identificador: str,
    sessao: Session,
) -> Estabelecimento:
    # Busca um estabelecimento pelo identificador e status ativo
    # Faz com que estabelecimentos inativos não sejam retornados no endpoint público
    consulta = select(Estabelecimento).where(
        Estabelecimento.identificador == identificador,
        Estabelecimento.ativo.is_(True),
    )
    estabelecimento = sessao.scalar(consulta)
    # Lança erro se não for encontrado
    if estabelecimento is None:
        raise EstabelecimentoNaoEncontradoError(
            "Estabelecimento não encontrado."
        )
    # Retorna o estabelecimento
    return estabelecimento

# Verifica se um valor único já pertence a outro estabelecimento
# O próprio estabelecimento é ignorado pra permitir enviar o valor atual
def _valor_em_uso_por_outro(
    coluna,
    valor: str,
    id_estabelecimento: int,
    sessao: Session,
) -> bool:
    consulta = select(Estabelecimento.id_estabelecimento).where(
        coluna == valor,
        Estabelecimento.id_estabelecimento != id_estabelecimento,
    )
    return sessao.scalar(consulta) is not None

# Atualização dos dados do estabelecimento autenticado
# Apenas os campos informados na requisição são alterados
def atualizar_estabelecimento(
    estabelecimento: Estabelecimento,
    dados: EstabelecimentoAtualizacao,
    sessao: Session,
) -> Estabelecimento:
    # exclude_unset=True exclui os campos não informados
    alteracoes = dados.model_dump(exclude_unset=True)
    id_estabelecimento = estabelecimento.id_estabelecimento
    # Verifica e-mail duplicado
    if "email" in alteracoes and _valor_em_uso_por_outro(
        Estabelecimento.email,
        alteracoes["email"],
        id_estabelecimento,
        sessao,
    ):
        raise EstabelecimentoDuplicadoError("E-mail já cadastrado.")
    # Verifica documento duplicado
    if "documento" in alteracoes and _valor_em_uso_por_outro(
        Estabelecimento.documento,
        alteracoes["documento"],
        id_estabelecimento,
        sessao,
    ):
        raise EstabelecimentoDuplicadoError("Documento já cadastrado.")
    # Verifica identificador duplicado
    if "identificador" in alteracoes and _valor_em_uso_por_outro(
        Estabelecimento.identificador,
        alteracoes["identificador"],
        id_estabelecimento,
        sessao,
    ):
        raise EstabelecimentoDuplicadoError("Identificador já cadastrado.")
    # A senha nunca é salva em texto: gera o hash e remove o campo senha
    if "senha" in alteracoes:
        estabelecimento.senha_hash = gerar_hash_senha(alteracoes.pop("senha"))
    # Altera os demais campos informados
    for campo, valor in alteracoes.items():
        setattr(estabelecimento, campo, valor)
    # Salva no db
    try:
        sessao.commit()
    # Levanta e retorna erro se houver algum dos dados duplicados
    except IntegrityError as erro:
        sessao.rollback()
        raise EstabelecimentoDuplicadoError(
            "E-mail, documento ou identificador já cadastrado."
        ) from erro
    sessao.refresh(estabelecimento)
    return estabelecimento
