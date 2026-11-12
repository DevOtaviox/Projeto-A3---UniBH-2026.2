from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.tokens import TokenInvalidoError, validar_token_acesso
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento

# Configura autenticação com token bearer
esquema_bearer = HTTPBearer(auto_error=False)

def obter_estabelecimento_atual(
    credenciais: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(esquema_bearer),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Estabelecimento:
    # Verifica credenciais da requisição
    if credenciais is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Valida token e extrai id estabelecimento
    try:
        id_estabelecimento = validar_token_acesso(
            credenciais.credentials
        )
    except TokenInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    # Consulta estabelecimento pelo id e cria objeto
    estabelecimento = sessao.get(
        Estabelecimento,
        id_estabelecimento,
    )
    # Verifica se o estabelecimento existe e é ativo
    if estabelecimento is None or not estabelecimento.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível autenticar a requisição.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return estabelecimento
