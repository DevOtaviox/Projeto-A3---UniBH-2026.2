from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.config import (
    ALGORITMO_JWT,
    SECRET_KEY,
    TEMPO_EXPIRACAO_TOKEN_MINUTOS,
)
from app.core.tokens import (
    TokenInvalidoError,
    criar_token_acesso,
    validar_token_acesso,
)


def test_criar_token_acesso():
    # Cria token
    token = criar_token_acesso(1)
    # Decodifica e verifica o token
    dados_token = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITMO_JWT],
    )
    # Resultado esperado e comparações
    assert dados_token["sub"] == "1"
    assert "iat" in dados_token
    assert "exp" in dados_token
    assert (
        dados_token["exp"] - dados_token["iat"]
        == TEMPO_EXPIRACAO_TOKEN_MINUTOS * 60
    )

def test_validar_token_acesso():
    # Cria token
    token = criar_token_acesso(1)
    # Valida o token
    id_estabelecimento = validar_token_acesso(token)
    # Resultado esperado e comparações
    assert id_estabelecimento == 1

def test_validar_token_acesso_assinatura_invalida():
    # Define dados para um token
    agora = datetime.now(UTC)
    dados_token = {
        "sub": "1",
        "iat": agora,
        "exp": agora + timedelta(minutes=5),
    }
    # Cria token com uma chave diferente da do .env
    token = jwt.encode(
        dados_token,
        f"{SECRET_KEY}-chave_diferente",
        algorithm=ALGORITMO_JWT,
    )
    # Tenta validar o token
    with pytest.raises(TokenInvalidoError):
        validar_token_acesso(token)

def test_validar_token_acesso_expirado():
    # Define dados para um token expirado
    agora = datetime.now(UTC)
    dados_token = {
        "sub": "1",
        "iat": agora - timedelta(minutes=2),
        "exp": agora - timedelta(minutes=1),
    }
    # Gera token expirado
    token = jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITMO_JWT,
    )
    # Tenta validar o token
    with pytest.raises(TokenInvalidoError):
        validar_token_acesso(token)

def test_validar_token_acesso_sem_identificador():
    # Define dados para token sem identificador
    agora = datetime.now(UTC)
    dados_token = {
        "iat": agora,
        "exp": agora + timedelta(minutes=5),
    }
    # Gera token sem o campo sub
    token = jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITMO_JWT,
    )
    # Tenta validar o token
    with pytest.raises(TokenInvalidoError):
        validar_token_acesso(token)

def test_validar_token_acesso_identificador_invalido():
    # Define dados para token com identificador invalido
    agora = datetime.now(UTC)
    dados_token = {
        "sub": "abc",
        "iat": agora,
        "exp": agora + timedelta(minutes=5),
    }
    # Cria token com identificador inválido
    token = jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITMO_JWT,
    )
    # Tenta validar o token
    with pytest.raises(TokenInvalidoError):
        validar_token_acesso(token)

def test_validar_token_acesso_malformado():
    # Cria um token com formato inválido
    token = "token-invalido"
    # Tenta validar o token
    with pytest.raises(TokenInvalidoError):
        validar_token_acesso(token)
