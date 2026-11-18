from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import EstabelecimentoCriacao, EstabelecimentoAtualizacao


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

def atualizar_estabelecimento(
    dados: EstabelecimentoAtualizacao,
    id_estabelecimento: int,
    sessao: Session,
) -> Estabelecimento:
    # Busca o estabelecimento pelo id
    estabelecimento = sessao.get(Estabelecimento, id_estabelecimento)
    # Lança erro se o estabelecimento não existir
    if estabelecimento is None:
        raise EstabelecimentoNaoEncontradoError(
            "Estabelecimento não encontrado."
        )
    # Verifica se o novo documento já pertence a outro estabelecimento
    if dados.documento is not None:
        consulta_documento = select(Estabelecimento.id_estabelecimento).where(
            Estabelecimento.documento == dados.documento,
            Estabelecimento.id_estabelecimento != id_estabelecimento,
        )
        if sessao.scalar(consulta_documento) is not None:
            raise EstabelecimentoDuplicadoError("Documento já cadastrado.")
    # Altera apenas os campos informados na requisição
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(estabelecimento, campo, valor)
    # Salva as alterações no db
    try:
        sessao.commit()
    # Trata possíveis conflitos de documento duplicado
    except IntegrityError as erro:
        sessao.rollback()
        raise EstabelecimentoDuplicadoError(
            "Documento já cadastrado."
        ) from erro
    # Atualiza os dados do objeto
    sessao.refresh(estabelecimento)
    return estabelecimento
