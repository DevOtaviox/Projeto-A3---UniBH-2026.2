import pytest
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoAtualizacao,
    EstabelecimentoCriacao,
    EstabelecimentoResposta,
)
from pydantic import ValidationError


def test_schema_estabelecimento_criacao_cpf():
    # Cria dados para criação do estabelecimento com CPF
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "12345678901",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Cria objeto usando o schema
    estabelecimento = EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    assert estabelecimento.nome == "Barbearia João"
    assert estabelecimento.endereco == "Rua das Flores, 100"
    assert estabelecimento.tipo_documento == "CPF"
    assert estabelecimento.documento == "12345678901"
    assert estabelecimento.identificador == "barbearia-joao"
    assert estabelecimento.email == "joao@example.com"
    assert estabelecimento.senha == "Senha123"
    assert estabelecimento.imagem is None

def test_schema_estabelecimento_criacao_cnpj():
    # Cria dados para criação do estabelecimento com CNPJ
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CNPJ",
        "documento": "12ABC34501DE35",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Cria objeto usando o schema
    estabelecimento = EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    assert estabelecimento.tipo_documento == "CNPJ"
    assert estabelecimento.documento == "12ABC34501DE35"

def test_schema_estabelecimento_cpf_invalido():
    # Cria dados com CPF contendo letras
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "1234567890A",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_cnpj_invalido():
    # Cria dados com CNPJ contendo letra nos dois últimos caracteres
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CNPJ",
        "documento": "12ABC34501DE3A",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_documento_tamanho_invalido():
    # Cria dados com CPF de tamanho incorreto
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "1234567890",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "Senha123",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_email_invalido():
    # Cria dados com endereço de e-mail inválido
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "12345678901",
        "identificador": "barbearia-joao",
        "email": "email-invalido",
        "senha": "Senha123",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_senha_invalida():
    # Cria dados com senha menor que oito caracteres
    dados = {
        "nome": "Barbearia João",
        "endereco": "Rua das Flores, 100",
        "tipo_documento": "CPF",
        "documento": "12345678901",
        "identificador": "barbearia-joao",
        "email": "joao@example.com",
        "senha": "1234567",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoCriacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_atualizacao():
    # Cria dados para atualização parcial
    dados = {
        "endereco": "Avenida Central, 200",
    }
    # Cria objeto com o schema de atualização
    estabelecimento = EstabelecimentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]
    # Resultado esperado e comparações
    # model_dump transforma o objeto em dicionário, campos não informados ficam como None
    # exclude_unset=True exclui os campos não informados
    assert estabelecimento.model_dump(exclude_unset=True) == {
        "endereco": "Avenida Central, 200",
    }

def test_schema_estabelecimento_atualizacao_vazia():
    # Cria dados sem campos para atualização
    dados = {}
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)

def test_schema_estabelecimento_atualizacao_nome_nulo():
    # Cria dados com nome nulo
    dados = {
        "nome": None,
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)

def test_schema_estabelecimento_atualizacao_documento_sem_tipo():
    # Cria dados com número de documento sem tipo
    dados = {
        "documento": "12345678901",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_atualizacao_tipo_sem_documento():
    # Cria dados com tipo de documento sem número
    dados = {
        "tipo_documento": "CPF",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_atualizacao_cpf_invalido():
    # Cria dados para atualização com CPF com letras
    dados = {
        "tipo_documento": "CPF",
        "documento": "1234567890A",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_atualizacao_cnpj_invalido():
    # Cria dados para atualização com CNPJ inválido
    dados = {
        "tipo_documento": "CNPJ",
        "documento": "12ABC34501DE3A",
    }
    # Tenta criar objeto usando o schema
    with pytest.raises(ValidationError):
        EstabelecimentoAtualizacao(**dados)  # pyright: ignore[reportArgumentType]

def test_schema_estabelecimento_resposta():
    # Cria objeto de estabelecimento
    estabelecimento = Estabelecimento(
        id_estabelecimento=1,
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        imagem=None,
        tipo_documento="CNPJ",
        documento="12ABC34501DE35",
        identificador="barbearia-joao",
        ativo=True,
        email="joao@example.com",
        senha_hash="hash_da_senha",
    )
    # Cria objeto com o schema de resposta usando o objeto de estabelecimento
    resposta = EstabelecimentoResposta.model_validate(estabelecimento)
    # Resultado esperado e comparações
    assert resposta.id_estabelecimento == 1
    assert resposta.nome == "Barbearia João"
    assert resposta.endereco == "Rua das Flores, 100"
    assert resposta.imagem is None
    assert resposta.tipo_documento == "CNPJ"
    assert resposta.documento == "12ABC34501DE35"
    assert resposta.identificador == "barbearia-joao"
    assert resposta.ativo is True
    assert resposta.email == "joao@example.com"
    # Verifica resposta sem hash da senha
    assert "senha_hash" not in resposta.model_dump()
