from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import EstabelecimentoCriacao


# Exceção para informações duplicadas
class EstabelecimentoDuplicadoError(Exception):
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
    # Levanta erro se houver algum dos dados duplicados
    except IntegrityError as erro:
        sessao.rollback()
        raise EstabelecimentoDuplicadoError(
            "E-mail, documento ou identificador já cadastrado."
        ) from erro
    # Atualiza os dados do objeto depois de criado no db, incluindo a pk
    sessao.refresh(estabelecimento)
    return estabelecimento
