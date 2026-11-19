import pytest
from pydantic import ValidationError

from app.schemas.autenticacao import AlteracaoSenhaRequisicao


def test_schema_alteracao_senha_valida():
    # Cria requisição com senhas válidas
    dados = AlteracaoSenhaRequisicao(
        senha_atual="Senha123",
        nova_senha="NovaSenha456",
    )
    # Resultado esperado e comparações
    assert dados.senha_atual == "Senha123"
    assert dados.nova_senha == "NovaSenha456"

def test_schema_alteracao_senha_nova_curta():
    # Nova senha com menos de 8 caracteres
    with pytest.raises(ValidationError):
        AlteracaoSenhaRequisicao(senha_atual="Senha123", nova_senha="curta")

def test_schema_alteracao_senha_nova_longa():
    # Nova senha com mais de 128 caracteres
    with pytest.raises(ValidationError):
        AlteracaoSenhaRequisicao(senha_atual="Senha123", nova_senha="a" * 129)

def test_schema_alteracao_senha_atual_vazia():
    # Senha atual vazia
    with pytest.raises(ValidationError):
        AlteracaoSenhaRequisicao(senha_atual="", nova_senha="NovaSenha456")

def test_schema_alteracao_senha_igual_atual():
    # Nova senha igual à atual
    with pytest.raises(ValidationError, match="diferente da atual"):
        AlteracaoSenhaRequisicao(senha_atual="Senha123", nova_senha="Senha123")
