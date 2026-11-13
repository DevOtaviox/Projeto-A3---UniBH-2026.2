from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verificar_senha
from app.core.tokens import criar_token_acesso
from app.models.estabelecimento import Estabelecimento
from app.schemas.autenticacao import LoginRequisicao


# Erro pra credencial invalida
class CredenciaisInvalidasError(Exception):
    pass

def autenticar_estabelecimento(
    dados: LoginRequisicao,
    sessao: Session,
) -> str:
    # Consulta estabelecimento por e-mail
    consulta = select(Estabelecimento).where(
        Estabelecimento.email == dados.email
    )
    estabelecimento = sessao.scalar(consulta)
    # Levanta erro pra inexistente ou inativo
    if estabelecimento is None or not estabelecimento.ativo:
        raise CredenciaisInvalidasError("E-mail ou senha incorretos.")
    # Verifica se senha corresponde ao hash
    if not verificar_senha(dados.senha, estabelecimento.senha_hash):
        raise CredenciaisInvalidasError("E-mail ou senha incorretos.")
    # Cria token com o id estabelecimento
    token = criar_token_acesso(estabelecimento.id_estabelecimento)
    return token
