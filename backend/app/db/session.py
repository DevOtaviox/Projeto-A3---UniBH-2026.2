from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Define a localização do banco SQLite
PASTA_DADOS = Path(__file__).resolve().parents[2] / "data"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
URL_BANCO = f"sqlite:///{PASTA_DADOS / 'agendamento.db'}"

# Cria a engine para conexão com o banco
def criar_engine(url_banco: str) -> Engine:
    argumentos_conexao = (
        {"check_same_thread": False}
        if url_banco.startswith("sqlite")
        else {}
    )
    return create_engine(
        url_banco,
        connect_args=argumentos_conexao,
    )

# Configura a engine e as sessões
motor_banco = criar_engine(URL_BANCO)
SessaoLocal = sessionmaker(
    bind=motor_banco,
)

# Função para fornecer sessão e fechar quando terminar a requisição
def obter_sessao_banco() -> Generator[Session, None, None]:
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
