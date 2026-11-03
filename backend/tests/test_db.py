from app.db import session
from app.db.base import BaseModelos
from app.models.estabelecimento import Estabelecimento
from sqlalchemy import inspect, text


# SQLAlchemy precisa dos imports de app.models.estabelecimento pra reconhecer os models para cada tabela
def test_conexao_com_sqlite(tmp_path):
    # Cria banco e engine do SQLAlchemy temporários
    url_banco = f"sqlite:///{tmp_path / 'teste.db'}"
    motor_teste = session.criar_engine(url_banco)
    try:
        # Abre conexão com o db usando a engine
        with motor_teste.connect() as conexao:
            # Consulta dado fictício e atribui o valor a variável resultado
            resultado = conexao.execute(text("SELECT 1")).scalar_one()
        # Resultado esperado e comparação
        assert resultado == 1
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()


def test_obter_sessao_banco():
    # Cria gerador de sessões
    gerador = session.obter_sessao_banco()
    try:
        # Cria a sessão
        sessao = next(gerador)
        # Consulta dado fictício e atribui o valor a variável resultado
        resultado = sessao.execute(text("SELECT 1")).scalar_one()
        # Resultado esperado e comparação
        assert resultado == 1
    # Fecha a engine do SQLAlchemy
    finally:
        gerador.close()


def test_tabela_estabelecimento(tmp_path):
    # Cria banco e engine do SQLAlchemy temporários
    url_banco = f"sqlite:///{tmp_path / 'teste.db'}"
    motor_teste = session.criar_engine(url_banco)
    try:
        # Cria as tabelas com os models do SQLAlchemy
        BaseModelos.metadata.create_all(motor_teste)
        # Cria um objeto para inspecionar o db
        inspecao = inspect(motor_teste)
        # Lista o nome de cada coluna
        colunas = {
            coluna["name"]
            for coluna in inspecao.get_columns("estabelecimento")
        }
        # Lista as colunas com restrições de unique na tabela
        restricoes_unicas = {
            tuple(restricao["column_names"])
            for restricao in inspecao.get_unique_constraints(
                "estabelecimento"
            )
        }
        # Lista os nomes das restrições de check
        restricoes_check = {
            restricao["name"]
            for restricao in inspecao.get_check_constraints(
                "estabelecimento"
            )
        }
        # Resultado esperado e comparações
        assert colunas == {
            "id_estabelecimento",
            "nome",
            "endereco",
            "imagem",
            "identificador",
            "ativo",
            "email",
            "senha_hash",
            "tipo_documento",
            "documento",
        }
        assert restricoes_unicas == {
            ("identificador",),
            ("email",),
            ("documento",),
        }
        assert restricoes_check == {
            "ck_estabelecimento_tipo_documento",
            "ck_estabelecimento_documento",
        }
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()
