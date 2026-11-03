from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Define a localização do banco SQLite e cria o diretório se não existir
PASTA_DADOS = Path(__file__).resolve().parents[2] / "data"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
URL_BANCO = f"sqlite:///{PASTA_DADOS / 'agendamento.db'}"

# Cria a engine para conexão com o banco
def criar_engine(url_banco: str) -> Engine:
    return create_engine(
        # Endereço do db
        url_banco,
        # Permite que o threads diferentes usem a mesma conexão, recomendado pro FastAPI mas não sei se vamos precisar
        connect_args={"check_same_thread": False},
    )

# Cria a engine para o banco definido na constante
motor_banco = criar_engine(URL_BANCO)

# Define SessaoLocal como função para criar nova sessão com o SQLAlchemy
SessaoLocal = sessionmaker(
    bind=motor_banco,
)

# Cria um gerador para criar sessões com o SessaoLocal e fechar quando a requisição terminar
# Esse é o que vamos usar nos endpoints para acesso ao db
def obter_sessao_banco() -> Generator[Session, None, None]:
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
