from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import obter_sessao_banco
from app.schemas.autenticacao import LoginRequisicao, LoginResposta
from app.services.autenticacao import (
    CredenciaisInvalidasError,
    autenticar_estabelecimento,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=LoginResposta)
def realizar_login(
    dados: LoginRequisicao,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> LoginResposta:
    # Cria token e faz a autenticação
    try:
        token = autenticar_estabelecimento(dados, sessao)
    # Resposta HTTP para credencial inválida
    except CredenciaisInvalidasError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(erro),
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro
    # Retorna o token
    return LoginResposta(access_token=token)
