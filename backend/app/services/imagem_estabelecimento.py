from pathlib import Path
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import DIRETORIO_IMAGENS
from app.models.estabelecimento import Estabelecimento
from app.services.estabelecimento import EstabelecimentoNaoEncontradoError

# Formatos de imagem permitidos
FORMATOS_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Tamanho máximo de 2 MB
TAMANHO_MAXIMO_IMAGEM = 2 * 1024 * 1024


# Exceção para imagem inválida
class ImagemInvalidaError(Exception):
    pass

# Exceção para imagem muito grande
class ImagemMuitoGrandeError(Exception):
    pass

# Valida se arquivo é realmente uma imagem e se sim retorna a extenão
def validar_imagem(
    conteudo: bytes,
    tipo_arquivo: str,
) -> str:
    # Verifica se a imagem está vazia
    if not conteudo:
        raise ImagemInvalidaError("A imagem não pode estar vazia.")
    # Verifica o tamanho da imagem
    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        raise ImagemMuitoGrandeError("A imagem deve ter no máximo 2 MB.")
    # Verifica se o formato é permitido
    if tipo_arquivo not in FORMATOS_PERMITIDOS:
        raise ImagemInvalidaError(
            "A imagem deve estar no formato JPEG, PNG ou WebP."
        )
    # Verifica a assinatura do arquivo
    if tipo_arquivo == "image/jpeg":
        formato_valido = conteudo.startswith(b"\xff\xd8\xff")
    elif tipo_arquivo == "image/png":
        formato_valido = conteudo.startswith(b"\x89PNG\r\n\x1a\n")
    else:
        formato_valido = (
            conteudo.startswith(b"RIFF")
            and conteudo[8:12] == b"WEBP"
        )
    # Lança erro se a assinatura não corresponder ao formato
    if not formato_valido:
        raise ImagemInvalidaError("O conteúdo da imagem é inválido.")
    # Retorna a extensão do arquivo
    return FORMATOS_PERMITIDOS[tipo_arquivo]

def salvar_imagem_estabelecimento(
    id_estabelecimento: int,
    conteudo: bytes,
    tipo_arquivo: str,
    sessao: Session,
) -> Estabelecimento:
    # Valida a imagem e obtém sua extensão
    extensao = validar_imagem(conteudo, tipo_arquivo)
    # Busca o estabelecimento pelo id do estabelecimento logado
    estabelecimento = sessao.get(Estabelecimento, id_estabelecimento)
    if estabelecimento is None:
        raise EstabelecimentoNaoEncontradoError(
            "Estabelecimento não encontrado."
        )
    # Guarda o caminho da imagem anterior antes de escrever o novo
    imagem_anterior = estabelecimento.imagem
    # Cria o diretório e um nome aleatorio para a imagem
    DIRETORIO_IMAGENS.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f"{uuid4().hex}{extensao}"
    caminho_arquivo = DIRETORIO_IMAGENS / nome_arquivo
    # Salva o arquivo e atualiza o caminho no db
    try:
        caminho_arquivo.write_bytes(conteudo)
        estabelecimento.imagem = f"/uploads/estabelecimentos/{nome_arquivo}"
        sessao.commit()
    # Remove o arquivo novo se não conseguir salvar
    except (OSError, SQLAlchemyError):
        sessao.rollback()
        caminho_arquivo.unlink(missing_ok=True)
        raise
    # Atualiza o objeto estabelecimento com uma consulta nova ao db
    sessao.refresh(estabelecimento)
    # Apaga a imagem anterior depois de salvar a nova
    if imagem_anterior and imagem_anterior.startswith(
        "/uploads/estabelecimentos/"
    ):
        caminho_anterior = DIRETORIO_IMAGENS / Path(imagem_anterior).name
        caminho_anterior.unlink(missing_ok=True)
    return estabelecimento

def remover_imagem_estabelecimento(
    id_estabelecimento: int,
    sessao: Session,
) -> Estabelecimento:
    # Busca o estabelecimento pelo id
    estabelecimento = sessao.get(Estabelecimento, id_estabelecimento)
    # Lança erro se o estabelecimento não existir
    if estabelecimento is None:
        raise EstabelecimentoNaoEncontradoError(
            "Estabelecimento não encontrado."
        )
    # Retorna o estabelecimento se não houver imagem
    if estabelecimento.imagem is None:
        return estabelecimento
    # Guarda o caminho da imagem antiga
    imagem_anterior = estabelecimento.imagem
    # Remove o caminho da imagem no db
    estabelecimento.imagem = None
    try:
        sessao.commit()
    # Desfaz a alteração se ocorrer erro no db
    except SQLAlchemyError:
        sessao.rollback()
        raise
    # Atualiza os dados do objeto
    sessao.refresh(estabelecimento)
    # Apaga o arquivo da imagem
    if imagem_anterior.startswith("/uploads/estabelecimentos/"):
        caminho_anterior = DIRETORIO_IMAGENS / Path(imagem_anterior).name
        caminho_anterior.unlink(missing_ok=True)
    return estabelecimento
