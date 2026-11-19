from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.schemas.autenticacao import (
    AlteracaoSenhaRequisicao,
    LoginRequisicao,
    LoginResposta,
)
from app.services.autenticacao import (
    CredenciaisInvalidasError,
    SenhaAtualIncorretaError,
    alterar_senha,
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

# Alteração de senha do estabelecimento autenticado
# Responde 204 sem corpo; o token atual continua válido
@router.patch("/senha", status_code=status.HTTP_204_NO_CONTENT)
def trocar_senha(
    dados: AlteracaoSenhaRequisicao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Response:
    try:
        alterar_senha(dados, estabelecimento.id_estabelecimento, sessao)
    # Responde como 400 se a senha atual estiver errada
    # Não usa 401 para o front-end não tratar como sessão expirada
    except SenhaAtualIncorretaError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(erro),
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
