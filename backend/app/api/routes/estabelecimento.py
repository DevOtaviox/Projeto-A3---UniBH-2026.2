from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import obter_estabelecimento_atual
from app.db.session import obter_sessao_banco
from app.models.estabelecimento import Estabelecimento
from app.schemas.estabelecimento import (
    EstabelecimentoAtualizacao,
    EstabelecimentoCriacao,
    EstabelecimentoPublicoResposta,
    EstabelecimentoResposta,
)
from app.services.estabelecimento import (
    EstabelecimentoDuplicadoError,
    EstabelecimentoNaoEncontradoError,
    atualizar_estabelecimento,
    buscar_estabelecimento_publico,
    cadastrar_estabelecimento,
)
from app.services.imagem_estabelecimento import (
    TAMANHO_MAXIMO_IMAGEM,
    ImagemInvalidaError,
    ImagemMuitoGrandeError,
    remover_imagem_estabelecimento,
    salvar_imagem_estabelecimento,
)

router = APIRouter(tags=["Estabelecimentos"])

# Cadastro de estabelecimento
@router.post(
    "/estabelecimentos",
    response_model=EstabelecimentoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_estabelecimento(
    dados: EstabelecimentoCriacao,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Estabelecimento:
    # Usa o service de cadastro
    try:
        estabelecimento = cadastrar_estabelecimento(dados, sessao)
    # Responde como 409 para erros de duplicidade retornados pelo service
    except EstabelecimentoDuplicadoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        ) from erro
    return estabelecimento

# Consulta dos dados do estabelecimento autenticado
@router.get(
    "/estabelecimentos/me",
    response_model=EstabelecimentoResposta,
)
def consultar_estabelecimento_atual(
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
) -> Estabelecimento:
    # Retorna o estabelecimento identificado pelo token
    return estabelecimento

@router.get(
    "/estabelecimentos/{identificador}",
    response_model=EstabelecimentoPublicoResposta,
)
def consultar_estabelecimento_publico(
    identificador: str,
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
):
    # Usa o service de consulta publica
    try:
        estabelecimento = buscar_estabelecimento_publico(identificador, sessao)
    # Responde como 404 para erro de não encontrado retornado pelo service
    except EstabelecimentoNaoEncontradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    return estabelecimento

# Atualização dos dados do estabelecimento autenticado
@router.patch(
    "/estabelecimentos/me",
    response_model=EstabelecimentoResposta,
)
def alterar_estabelecimento(
    dados: EstabelecimentoAtualizacao,
    estabelecimento: Annotated[
        Estabelecimento,
        Depends(obter_estabelecimento_atual),
    ],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
) -> Estabelecimento:
    # Usa o service de atualização com o id do estabelecimento autenticado
    try:
        estabelecimento_atualizado = atualizar_estabelecimento(
            dados,
            estabelecimento.id_estabelecimento,
            sessao,
        )
    # Responde como 404 se o estabelecimento não for encontrado
    except EstabelecimentoNaoEncontradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
    # Responde como 409 se o documento já estiver cadastrado
    except EstabelecimentoDuplicadoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        ) from erro
    return estabelecimento_atualizado

@router.post(
    "/estabelecimentos/me/imagem",
    response_model=EstabelecimentoResposta,
)
async def enviar_imagem_estabelecimento(
    arquivo: Annotated[UploadFile, File()],
    estabelecimento_atual: Annotated[Estabelecimento, Depends(obter_estabelecimento_atual)],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
):
    # Lê o arquivo até o limite permitido mais um byte
    # Evita ler um arquivo inteiro se ele for grande demais
    # Se o arquivo for maior que 2MB, o endpoint ainda lê até 2MB + 1 e o service ainda lança erro
    conteudo = await arquivo.read(TAMANHO_MAXIMO_IMAGEM + 1)
    # Salva ou substitui a imagem do estabelecimento autenticado
    try:
        return salvar_imagem_estabelecimento(
            estabelecimento_atual.id_estabelecimento,
            conteudo,
            arquivo.content_type or "",
            sessao,
        )
    # Retorna 413 se a imagem ultrapassar o tamanho permitido
    except ImagemMuitoGrandeError as erro:
        raise HTTPException(
            status_code=413,
            detail=str(erro),
        ) from erro
    # Retorna 422 se a imagem for inválida
    except ImagemInvalidaError as erro:
        raise HTTPException(
            status_code=422,
            detail=str(erro),
        ) from erro

@router.delete(
    "/estabelecimentos/me/imagem",
    response_model=EstabelecimentoResposta,
)
def excluir_imagem_estabelecimento(
    estabelecimento_atual: Annotated[Estabelecimento, Depends(obter_estabelecimento_atual)],
    sessao: Annotated[Session, Depends(obter_sessao_banco)],
):
    # Remove a imagem do estabelecimento autenticado
    return remover_imagem_estabelecimento(
        estabelecimento_atual.id_estabelecimento,
        sessao,
    )
