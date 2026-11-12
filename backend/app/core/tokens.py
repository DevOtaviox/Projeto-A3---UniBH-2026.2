from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import (
    ALGORITMO_JWT,
    SECRET_KEY,
    TEMPO_EXPIRACAO_TOKEN_MINUTOS,
)


# Erro pra token invalido
class TokenInvalidoError(Exception):
    pass

def criar_token_acesso(id_estabelecimento: int) -> str:
    # Horário atual
    agora = datetime.now(UTC)
    # DAdos do token
    dados_token = {
        "sub": str(id_estabelecimento),
        "iat": agora,
        "exp": agora + timedelta(minutes=TEMPO_EXPIRACAO_TOKEN_MINUTOS),
    }
    # Cria token com a chave do python-dotenv
    token = jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITMO_JWT,
    )
    return token

# Valida token e retorna id do estabelecimento
def validar_token_acesso(token: str) -> int:
    try:
        # Decodifica e verifica o token
        dados_token = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITMO_JWT],
            options={"require": ["sub", "iat", "exp"]},
        )
        # Extrai id do estabelecimento
        id_estabelecimento = int(dados_token["sub"])
        # Verifica se o id é valido
        if id_estabelecimento <= 0:
            raise ValueError("Identificador inválido.")
        return id_estabelecimento
    # Lança erro de token inválido se falhar
    except (jwt.InvalidTokenError, TypeError, ValueError) as erro:
        raise TokenInvalidoError("Token inválido ou expirado.") from erro
