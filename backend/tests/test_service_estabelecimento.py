import pytest
from sqlalchemy.orm import sessionmaker

from app.core.security import verificar_senha
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoAtualizacao,
    EstabelecimentoCriacao,
)
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    EstabelecimentoNaoEncontradoError,
    atualizar_estabelecimento,
    buscar_estabelecimento_publico,
    cadastrar_estabelecimento,
)


# Cria dados para cadastro
def criar_dados_estabelecimento(
    email="joao@example.com",
    documento="12345678901",
    identificador="barbearia-joao",
):
    return EstabelecimentoCriacao(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento=documento,
        identificador=identificador,
        email=email,
        senha="Senha123",
    )

def test_cadastrar_estabelecimento(sessao_teste):
    # Cria dados para cadastro
    dados = criar_dados_estabelecimento()
    # Cadastra o estabelecimento usando o Service
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Cria um gerador de sessões para consulta
    gerador_sessoes = sessionmaker(bind=sessao_teste.get_bind())
    with gerador_sessoes() as sessao_consulta:
        estabelecimento_salvo = sessao_consulta.get(
            Estabelecimento,
            estabelecimento.id_estabelecimento,
        )
    # Resultado esperado e comparações
    assert estabelecimento_salvo is not None
    assert estabelecimento_salvo.nome == "Barbearia João"
    assert estabelecimento_salvo.endereco == "Rua das Flores, 100"
    assert estabelecimento_salvo.tipo_documento == "CPF"
    assert estabelecimento_salvo.documento == "12345678901"
    assert estabelecimento_salvo.identificador == "barbearia-joao"
    assert estabelecimento_salvo.email == "joao@example.com"
    assert estabelecimento_salvo.ativo is True

def test_cadastrar_estabelecimento_hashing(sessao_teste):
    # Cria dados para cadastro
    dados = criar_dados_estabelecimento()
    # Cadastra o estabelecimento usando o Service
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Verifica hash da senha
    assert estabelecimento.senha_hash != dados.senha
    assert verificar_senha(dados.senha, estabelecimento.senha_hash) is True

def test_cadastrar_estabelecimento_email_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com e-mail duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="joao@example.com",
        documento="98765432100",
        identificador="barbearia-maria",
    )
    # Tenta cadastrar estabelecimento com e-mail duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)

def test_cadastrar_estabelecimento_documento_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com documento duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="12345678901",
        identificador="barbearia-maria",
    )
    # Tenta cadastrar estabelecimento com documento duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)

def test_cadastrar_estabelecimento_identificador_duplicado(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados com identificador duplicado
    dados_duplicados = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="98765432100",
        identificador="barbearia-joao",
    )
    # Tenta cadastrar estabelecimento com identificador duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        cadastrar_estabelecimento(dados_duplicados, sessao_teste)

def test_buscar_estabelecimento_publico_ativo(sessao_teste):
    # Cria estabelecimento e adiciona ao db
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        ativo=True,
        email="joao@example.com",
        senha_hash="hash_da_senha",
    )
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    # Busca pelo identificador
    resultado = buscar_estabelecimento_publico("barbearia-joao", sessao_teste)
    # Resultado esperado e comparação
    assert resultado.id_estabelecimento == estabelecimento.id_estabelecimento
    assert resultado.identificador == "barbearia-joao"
    assert resultado.ativo is True

def test_buscar_estabelecimento_publico_inexistente(sessao_teste):
    # Identificador que não existe no db
    identificador = "inexistente"
    # Tenta buscar o estabelecimento
    with pytest.raises(EstabelecimentoNaoEncontradoError):
        buscar_estabelecimento_publico(identificador, sessao_teste)

def test_buscar_estabelecimento_publico_inativo(sessao_teste):
    # Cria um estabelecimento inativo
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        ativo=False,
        email="joao@example.com",
        senha_hash="hash_da_senha",
    )
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    # Tenta buscar o estabelecimento
    with pytest.raises(EstabelecimentoNaoEncontradoError):
        buscar_estabelecimento_publico("barbearia-joao", sessao_teste)

def test_atualizar_estabelecimento(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados para atualização parcial
    dados_atualizacao = EstabelecimentoAtualizacao(nome="Barbearia Central")
    # Atualiza o estabelecimento usando o Service
    atualizar_estabelecimento(
        dados_atualizacao,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Cria um gerador de sessões para consulta
    gerador_sessoes = sessionmaker(bind=sessao_teste.get_bind())
    with gerador_sessoes() as sessao_consulta:
        estabelecimento_salvo = sessao_consulta.get(
            Estabelecimento,
            estabelecimento.id_estabelecimento,
        )
    # Resultado esperado e comparações
    assert estabelecimento_salvo is not None
    assert estabelecimento_salvo.nome == "Barbearia Central"
    assert estabelecimento_salvo.endereco == "Rua das Flores, 100"
    assert estabelecimento_salvo.documento == "12345678901"
    assert estabelecimento_salvo.identificador == "barbearia-joao"
    assert estabelecimento_salvo.email == "joao@example.com"

def test_atualizar_estabelecimento_documento_duplicado(sessao_teste):
    # Cria e cadastra dois estabelecimentos
    dados = criar_dados_estabelecimento()
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    dados_outro = criar_dados_estabelecimento(
        email="maria@example.com",
        documento="98765432100",
        identificador="manicure-maria",
    )
    cadastrar_estabelecimento(dados_outro, sessao_teste)
    # Cria dados com documento já cadastrado
    dados_atualizacao = EstabelecimentoAtualizacao(
        tipo_documento="CPF",
        documento="98765432100",
    )
    # Tenta atualizar com documento duplicado
    with pytest.raises(EstabelecimentoDuplicadoError):
        atualizar_estabelecimento(
            dados_atualizacao,
            estabelecimento.id_estabelecimento,
            sessao_teste,
        )

def test_atualizar_estabelecimento_mesmo_documento(sessao_teste):
    # Cria e cadastra estabelecimento
    dados = criar_dados_estabelecimento()
    estabelecimento = cadastrar_estabelecimento(dados, sessao_teste)
    # Cria dados mantendo o mesmo documento
    dados_atualizacao = EstabelecimentoAtualizacao(
        tipo_documento="CPF",
        documento="12345678901",
    )
    # Atualiza o estabelecimento usando o Service
    resultado = atualizar_estabelecimento(
        dados_atualizacao,
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Resultado esperado e comparações
    assert resultado.documento == "12345678901"
    assert resultado.tipo_documento == "CPF"

def test_atualizar_estabelecimento_inexistente(sessao_teste):
    # Cria dados para atualização
    dados = EstabelecimentoAtualizacao(nome="Barbearia Teste")
    # Tenta atualizar um estabelecimento inexistente
    with pytest.raises(EstabelecimentoNaoEncontradoError):
        atualizar_estabelecimento(
            dados,
            999,
            sessao_teste,
        )
