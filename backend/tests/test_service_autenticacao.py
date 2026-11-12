import pytest
from app.core.security import gerar_hash_senha
from app.core.tokens import validar_token_acesso
from app.models.estabelecimento import Estabelecimento
from app.schemas.autenticacao import LoginRequisicao
from app.services.autenticacao import (
    CredenciaisInvalidasError,
    autenticar_estabelecimento,
)


# Cria estabelecimento de teste
def criar_estabelecimento(
    sessao_teste,
    email="joao@example.com",
    senha="Senha123",
    ativo=True,
):
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        email=email,
        senha_hash=gerar_hash_senha(senha),
        ativo=ativo,
    )
    # Salva no banco e retorna como objeto com id
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

def test_autenticar_estabelecimento(sessao_teste):
    # Cria objeto estabelecimento
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Cria dados para autenticação
    dados = LoginRequisicao(
        email="joao@example.com",
        senha="Senha123",
    )
    # Autentica usando o Service
    token = autenticar_estabelecimento(dados, sessao_teste)
    # Valida o token e obtém o identificador
    id_estabelecimento = validar_token_acesso(token)
    # Resultado esperado e comparações
    assert isinstance(token, str)
    assert id_estabelecimento == estabelecimento.id_estabelecimento

def test_autenticar_estabelecimento_email_inexistente(sessao_teste):
    # Cria dados com e-mail inexistente
    dados = LoginRequisicao(
        email="emailinexistente@example.com",
        senha="Senha123",
    )
    # Tenta autenticar
    with pytest.raises(CredenciaisInvalidasError):
        autenticar_estabelecimento(dados, sessao_teste)

def test_autenticar_estabelecimento_senha_incorreta(sessao_teste):
    # Cria estabelecimento
    criar_estabelecimento(sessao_teste)
    # Cria dados com senha incorreta
    dados = LoginRequisicao(
        email="joao@example.com",
        senha="Senha321",
    )
    # Tenta autenticar
    with pytest.raises(CredenciaisInvalidasError):
        autenticar_estabelecimento(dados, sessao_teste)

def test_autenticar_estabelecimento_inativo(sessao_teste):
    # Cria estabelecimento com estado como inativo
    criar_estabelecimento(sessao_teste, ativo=False)
    # Cria dados para autenticação
    dados = LoginRequisicao(
        email="joao@example.com",
        senha="Senha123",
    )
    # Tenta autenticar
    with pytest.raises(CredenciaisInvalidasError):
        autenticar_estabelecimento(dados, sessao_teste)
