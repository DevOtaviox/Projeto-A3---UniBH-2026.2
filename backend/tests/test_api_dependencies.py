from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.api.dependencies import obter_estabelecimento_atual
from app.core.config import ALGORITMO_JWT, SECRET_KEY
from app.core.tokens import criar_token_acesso
from app.models.estabelecimento import Estabelecimento
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


# Cria estabelecimento de teste
def criar_estabelecimento(sessao_teste, ativo=True):
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        email="joao@example.com",
        senha_hash="hash-teste",
        ativo=ativo,
    )
    # Adiciona e salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

def test_obter_estabelecimento_atual(sessao_teste):
    # Cria estabelecimento
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Cria token
    token = criar_token_acesso(estabelecimento.id_estabelecimento)
    # Cria credenciais com o token
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    # Extrai o estabelecimento autenticado
    resultado = obter_estabelecimento_atual(credenciais, sessao_teste)
    # Resultado esperado e comparações
    assert resultado.id_estabelecimento == estabelecimento.id_estabelecimento
    assert resultado.email == "joao@example.com"
    assert resultado.ativo is True

def test_obter_estabelecimento_sem_token(sessao_teste):
    # Faz requisição sem credencial e token
    with pytest.raises(HTTPException) as erro:
        obter_estabelecimento_atual(None, sessao_teste)
    # Resultado esperado e comparações
    assert erro.value.status_code == 401

def test_obter_estabelecimento_token_assinatura_invalida(sessao_teste):
    # Define dados para token
    agora = datetime.now(UTC)
    dados_token = {
        "sub": "1",
        "iat": agora,
        "exp": agora + timedelta(minutes=5),
    }
    # Cria token com chave diferente do .env
    token = jwt.encode(
        dados_token,
        f"{SECRET_KEY}-diferente",
        algorithm=ALGORITMO_JWT,
    )
    # Cria credenciais com o token
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    # Tenta obter estabelecimento
    with pytest.raises(HTTPException) as erro:
        obter_estabelecimento_atual(credenciais, sessao_teste)
    # Resultado esperado e comparações
    assert erro.value.status_code == 401


def test_obter_estabelecimento_token_expirado(sessao_teste):
    # Dados para token expirado
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
    # Cria credenciais com o token
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    # Tenta obter estabelecimento
    with pytest.raises(HTTPException) as erro:
        obter_estabelecimento_atual(credenciais, sessao_teste)
    # Resultado esperado e comparações
    assert erro.value.status_code == 401


def test_obter_estabelecimento_inexistente(sessao_teste):
    # Cria token para um estabelecimento inexistente
    token = criar_token_acesso(999)
    # Cria credenciais
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    # Tenta obter estabelecimento
    with pytest.raises(HTTPException) as erro:
        obter_estabelecimento_atual(credenciais, sessao_teste)
    # Resultado esperado e comparações
    assert erro.value.status_code == 401


def test_obter_estabelecimento_inativo(sessao_teste):
    # Cria estabelecimento inativo
    estabelecimento = criar_estabelecimento(sessao_teste, ativo=False)
    # Gera token
    token = criar_token_acesso(estabelecimento.id_estabelecimento)
    # Cria credenciais
    credenciais = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    # Tenta obter estabelecimento
    with pytest.raises(HTTPException) as erro:
        obter_estabelecimento_atual(credenciais, sessao_teste)
    # Resultado esperado e comparações
    assert erro.value.status_code == 401
