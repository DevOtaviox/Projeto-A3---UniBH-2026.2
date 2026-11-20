from pathlib import Path

import pytest

from app.models.estabelecimento import Estabelecimento
from app.services.estabelecimento import EstabelecimentoNaoEncontradoError
from app.services.imagem_estabelecimento import (
    TAMANHO_MAXIMO_IMAGEM,
    ImagemInvalidaError,
    ImagemMuitoGrandeError,
    remover_imagem_estabelecimento,
    salvar_imagem_estabelecimento,
    validar_imagem,
)


def test_validar_imagem_jpeg():
    # Cria conteúdo com assinatura JPEG
    conteudo = b"\xff\xd8\xff" + b"conteudo-imagem"
    # Valida a imagem
    extensao = validar_imagem(conteudo, "image/jpeg")
    # Resultado esperado e comparações
    assert extensao == ".jpg"

def test_validar_imagem_png():
    # Cria conteúdo com assinatura PNG
    conteudo = b"\x89PNG\r\n\x1a\n" + b"conteudo-imagem"
    # Valida a imagem
    extensao = validar_imagem(conteudo, "image/png")
    # Resultado esperado e comparações
    assert extensao == ".png"

def test_validar_imagem_webp():
    # Cria conteúdo com assinatura WebP
    conteudo = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"conteudo"
    # Valida a imagem
    extensao = validar_imagem(conteudo, "image/webp")
    # Resultado esperado e comparações
    assert extensao == ".webp"

def test_validar_imagem_vazia():
    # Cria conteúdo vazio
    conteudo = b""
    # Tenta validar a imagem
    with pytest.raises(ImagemInvalidaError):
        validar_imagem(conteudo, "image/png")

def test_validar_imagem_muito_grande():
    # Cria conteúdo maior que 2 MB
    conteudo = b"\xff\xd8\xff" + b"a" * TAMANHO_MAXIMO_IMAGEM
    # Tenta validar a imagem
    with pytest.raises(ImagemMuitoGrandeError):
        validar_imagem(conteudo, "image/jpeg")

def test_validar_imagem_formato_invalido():
    # Cria conteúdo de arquivo com formato não permitido
    conteudo = b"conteudo-arquivo"
    # Tenta validar o arquivo
    with pytest.raises(ImagemInvalidaError):
        validar_imagem(conteudo, "application/pdf")

def test_validar_imagem_assinatura_invalida():
    # Cria conteúdo sem assinatura de imagem
    conteudo = b"arquivo-invalido"
    # Tenta validar como PNG
    with pytest.raises(ImagemInvalidaError):
        validar_imagem(conteudo, "image/png")

def test_validar_imagem_formato_diferente_do_conteudo():
    # Cria conteúdo com assinatura JPEG
    conteudo = b"\xff\xd8\xff" + b"conteudo-imagem"
    # Tenta validar o conteúdo como PNG
    with pytest.raises(ImagemInvalidaError):
        validar_imagem(conteudo, "image/png")

# Cria estabelecimento de teste
def criar_estabelecimento(sessao_teste):
    estabelecimento = Estabelecimento(
        nome="Barbearia João",
        endereco="Rua das Flores, 100",
        tipo_documento="CPF",
        documento="12345678901",
        identificador="barbearia-joao",
        email="joao@example.com",
        senha_hash="hash-teste",
    )
    # Adiciona e salva no db
    sessao_teste.add(estabelecimento)
    sessao_teste.commit()
    sessao_teste.refresh(estabelecimento)
    return estabelecimento

def test_salvar_imagem_estabelecimento(sessao_teste, tmp_path, monkeypatch):
    # Usa diretório temporário para imagens
    monkeypatch.setattr(
        "app.services.imagem_estabelecimento.DIRETORIO_IMAGENS",
        tmp_path,
    )
    # Cria estabelecimento sem imagem
    estabelecimento = criar_estabelecimento(sessao_teste)
    conteudo = b"\x89PNG\r\n\x1a\n" + b"conteudo-imagem"
    # Salva a imagem usando o Service
    resultado = salvar_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        conteudo,
        "image/png",
        sessao_teste,
    )
    # Verifica o caminho salvo e o conteúdo do arquivo
    assert resultado.imagem is not None
    assert resultado.imagem.startswith("/uploads/estabelecimentos/")
    caminho = tmp_path / Path(resultado.imagem).name
    assert caminho.is_file()
    assert caminho.read_bytes() == conteudo
    # Verifica o caminho armazenado no banco
    sessao_teste.refresh(estabelecimento)
    assert estabelecimento.imagem == resultado.imagem

def test_substituir_imagem_estabelecimento(sessao_teste, tmp_path, monkeypatch):
    # Usa diretório temporário para imagens
    monkeypatch.setattr(
        "app.services.imagem_estabelecimento.DIRETORIO_IMAGENS",
        tmp_path,
    )
    # Cria estabelecimento
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Salva a primeira imagem
    primeira = salvar_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        b"\x89PNG\r\n\x1a\n" + b"primeira-imagem",
        "image/png",
        sessao_teste,
    )
    # Guarda o caminho da primeira imagem
    assert primeira.imagem is not None
    imagem_anterior = primeira.imagem
    caminho_anterior = tmp_path / Path(imagem_anterior).name
    # Substitui pela segunda imagem
    segunda = salvar_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        b"\xff\xd8\xff" + b"segunda-imagem",
        "image/jpeg",
        sessao_teste,
    )
    # Verifica o caminho da imagem nova
    assert segunda.imagem is not None
    caminho_novo = tmp_path / Path(segunda.imagem).name
    # Resultado esperado e comparações
    assert segunda.imagem.endswith(".jpg")
    assert caminho_novo.is_file()
    assert not caminho_anterior.exists()
    assert segunda.imagem != imagem_anterior

def test_remover_imagem_estabelecimento(sessao_teste, tmp_path, monkeypatch):
    # Usa diretório temporário para imagem
    monkeypatch.setattr(
        "app.services.imagem_estabelecimento.DIRETORIO_IMAGENS",
        tmp_path,
    )
    # Cria estabelecimento e salva uma imagem
    estabelecimento = criar_estabelecimento(sessao_teste)
    resultado = salvar_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        b"\x89PNG\r\n\x1a\n" + b"conteudo-imagem",
        "image/png",
        sessao_teste,
    )
    # Guarda o caminho da imagem salva
    assert resultado.imagem is not None
    caminho_imagem = tmp_path / Path(resultado.imagem).name
    assert caminho_imagem.is_file()
    # Remove a imagem usando o service
    resultado = remover_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Verifica se a imagem foi removida do disco e do db
    assert resultado.imagem is None
    assert not caminho_imagem.exists()
    sessao_teste.refresh(estabelecimento)
    assert estabelecimento.imagem is None

def test_remover_imagem_nao_definida(sessao_teste):
    # Cria estabelecimento sem imagem
    estabelecimento = criar_estabelecimento(sessao_teste)
    # Tenta remover a imagem
    resultado = remover_imagem_estabelecimento(
        estabelecimento.id_estabelecimento,
        sessao_teste,
    )
    # Verifica se campo continua none
    assert resultado.imagem is None

def test_remover_imagem_estabelecimento_inexistente(sessao_teste):
    # Tenta remover imagem de estabelecimento inexistente
    with pytest.raises(EstabelecimentoNaoEncontradoError):
        remover_imagem_estabelecimento(
            999,
            sessao_teste,
        )
