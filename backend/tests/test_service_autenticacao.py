import pytest

from app.core.security import gerar_hash_senha, verificar_senha
from app.core.tokens import validar_token_acesso
from app.models.estabelecimento import Estabelecimento
from app.schemas.autenticacao import AlteracaoSenhaRequisicao, LoginRequisicao
from app.services.autenticacao import (
    CredenciaisInvalidasError,
    SenhaAtualIncorretaError,
    alterar_senha,
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

def test_alterar_senha(sessao_teste):
    # Cria estabelecimento com a senha atual
    estabelecimento = criar_estabelecimento(sessao_teste)
    dados = AlteracaoSenhaRequisicao(
        senha_atual="Senha123",
        nova_senha="NovaSenha456",
    )
    # Altera a senha
    alterar_senha(dados, estabelecimento.id_estabelecimento, sessao_teste)
    sessao_teste.refresh(estabelecimento)
    # A nova senha passa a valer e a antiga não
    assert verificar_senha("NovaSenha456", estabelecimento.senha_hash)
    assert not verificar_senha("Senha123", estabelecimento.senha_hash)
    # Login funciona com a nova senha
    token = autenticar_estabelecimento(
        LoginRequisicao(email="joao@example.com", senha="NovaSenha456"),
        sessao_teste,
    )
    assert validar_token_acesso(token) == estabelecimento.id_estabelecimento

def test_alterar_senha_atual_incorreta(sessao_teste):
    # Cria estabelecimento
    estabelecimento = criar_estabelecimento(sessao_teste)
    hash_anterior = estabelecimento.senha_hash
    dados = AlteracaoSenhaRequisicao(
        senha_atual="SenhaErrada",
        nova_senha="NovaSenha456",
    )
    # Tenta alterar com a senha atual errada
    with pytest.raises(SenhaAtualIncorretaError):
        alterar_senha(dados, estabelecimento.id_estabelecimento, sessao_teste)
    # O hash não muda
    sessao_teste.refresh(estabelecimento)
    assert estabelecimento.senha_hash == hash_anterior

def test_alterar_senha_estabelecimento_inexistente(sessao_teste):
    # Id que não existe no db
    dados = AlteracaoSenhaRequisicao(
        senha_atual="Senha123",
        nova_senha="NovaSenha456",
    )
    with pytest.raises(SenhaAtualIncorretaError):
        alterar_senha(dados, 999, sessao_teste)
