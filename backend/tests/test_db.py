from app.db import session
from sqlalchemy import text


def test_conexao_com_sqlite(tmp_path):
    url_banco = f"sqlite:///{tmp_path / 'teste.db'}"
    motor_teste = session.criar_engine(url_banco)
    try:
        with motor_teste.connect() as conexao:
            resultado = conexao.execute(
                text("SELECT 1")
            ).scalar_one()
        assert resultado == 1
    finally:
        motor_teste.dispose()


def test_obter_sessao_banco():
    gerador = session.obter_sessao_banco()
    try:
        sessao = next(gerador)
        resultado = sessao.execute(text("SELECT 1")).scalar_one()
        assert resultado == 1
    finally:
        gerador.close()
