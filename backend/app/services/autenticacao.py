from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha, verificar_senha
from app.core.tokens import criar_token_acesso
from app.models.estabelecimento import Estabelecimento
from app.schemas.autenticacao import AlteracaoSenhaRequisicao, LoginRequisicao


# Erro pra credencial invalida
class CredenciaisInvalidasError(Exception):
    pass

# Erro pra senha atual incorreta na alteração de senha
class SenhaAtualIncorretaError(Exception):
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

# Altera a senha do estabelecimento autenticado
# O id_estabelecimento vem do token, então só altera a própria senha
def alterar_senha(
    dados: AlteracaoSenhaRequisicao,
    id_estabelecimento: int,
    sessao: Session,
) -> None:
    estabelecimento = sessao.get(Estabelecimento, id_estabelecimento)
    # Confere a senha atual antes de trocar
    if estabelecimento is None or not verificar_senha(
        dados.senha_atual,
        estabelecimento.senha_hash,
    ):
        raise SenhaAtualIncorretaError("Senha atual incorreta.")
    # Salva só o hash da nova senha
    estabelecimento.senha_hash = gerar_hash_senha(dados.nova_senha)
    sessao.commit()
