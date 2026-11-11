import app.models  # noqa: F401
import pytest
from app.db import session
from app.db.base import BaseModelos
from sqlalchemy.orm import sessionmaker


# Fixture com o gerador de sessões
# Cria uma sessão temporária com odb
@pytest.fixture
def sessao_teste(tmp_path):
    # Cria banco e engine do SQLAlchemy temporários
    url_banco = f"sqlite:///{tmp_path / 'teste.db'}"
    motor_teste = session.criar_engine(url_banco)
    try:
        # Cria as tabelas com os models do SQLAlchemy
        BaseModelos.metadata.create_all(bind=motor_teste)
        # Cria um gerador com a engine do teste
        gerador_sessoes = sessionmaker(bind=motor_teste)
        # Abre sessão
        sessao = gerador_sessoes()
        try:
            yield sessao
        finally:
            # Fecha a sessão do SQLAlchemy
            sessao.close()
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()
