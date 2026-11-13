from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Define a localização do banco SQLite e cria o diretório se não existir
PASTA_DADOS = Path(__file__).resolve().parents[2] / "data"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
URL_BANCO = f"sqlite:///{PASTA_DADOS / 'agendamento.db'}"

# Ativa a validação de chaves estrangeiras no SQLite
# O SQLite não valida FKs por padrão
# Essa função serve pra validar se uma FK existe na outra tabela antes de cadastrar uma informação
def ativar_chaves_estrangeiras(conexao, registro):
    # Guarda a configuração de autocommit da conexão
    autocommit_anterior = conexao.autocommit
    # Ativa temporariamente o autocommit
    conexao.autocommit = True
    # Ativa a validação de chaves estrangeiras no SQLite
    try:
        cursor = conexao.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
    # Restaura a configuração de autocommit da conexão
    finally:
        conexao.autocommit = autocommit_anterior

# Cria a engine para conexão com o banco
def criar_engine(url_banco: str) -> Engine:
    motor = create_engine(
        # Endereço do db
        url_banco,
        # Permite que threads diferentes utilizem a conexão
        connect_args={"check_same_thread": False},
    )
    # Ativa a validação de FKs
    event.listen(motor, "connect", ativar_chaves_estrangeiras)

    return motor

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
