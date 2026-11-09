import pytest
from app.db import session
from app.db.base import BaseModelos
from app.models.agendamento import Agendamento
from app.models.estabelecimento import Estabelecimento
from app.models.horario_funcionamento import HorarioFuncionamento
from app.models.servico import Servico
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


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
            for restricao in inspecao.get_unique_constraints("estabelecimento")
        }
        # Lista os nomes das restrições de check
        restricoes_check = {
            restricao["name"]
            for restricao in inspecao.get_check_constraints("estabelecimento")
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

def test_rejeitar_servico_com_estabelecimento_inexistente(tmp_path):
    # Cria banco e engine do SQLAlchemy temporários
    url_banco = f"sqlite:///{tmp_path / 'teste.db'}"
    motor_teste = session.criar_engine(url_banco)
    try:
        # Cria as tabelas com os models do SQLAlchemy
        BaseModelos.metadata.create_all(motor_teste)
        # Tenta cadastrar serviço com estabelecimento inexistente
        # Espera um IntegrityError como resultado
        with pytest.raises(IntegrityError), motor_teste.begin() as conexao:
            conexao.execute(
                text("""
                        INSERT INTO servico (
                            id_estabelecimento,
                            nome,
                            preco,
                            duracao_minutos,
                            ativo
                        )
                        VALUES (
                            :id_estabelecimento,
                            :nome,
                            :preco,
                            :duracao_minutos,
                            :ativo
                        )
                    """),
                {
                    "id_estabelecimento": 999,
                    "nome": "Corte de cabelo",
                    "preco": 35.00,
                    "duracao_minutos": 30,
                    "ativo": True,
                }
            )
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()

def test_tabela_horario_funcionamento(tmp_path):
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
            for coluna in inspecao.get_columns("horario_funcionamento")
        }
        # Lista as colunas com restrições de unique na tabela
        restricoes_unicas = {
            tuple(restricao["column_names"])
            for restricao in inspecao.get_unique_constraints("horario_funcionamento")
        }
        # Lista os nomes das restrições de check
        restricoes_check = {
            restricao["name"]
            for restricao in inspecao.get_check_constraints("horario_funcionamento")
        }
        # Lista as chaves estrangeiras da tabela
        chaves_estrangeiras = {
            (
                tuple(chave["constrained_columns"]),
                chave["referred_table"],
                tuple(chave["referred_columns"]),
            )
            for chave in inspecao.get_foreign_keys(
                "horario_funcionamento"
            )
        }
        # Resultado esperado e comparações
        assert colunas == {
            "id_horario",
            "id_estabelecimento",
            "segunda",
            "terca",
            "quarta",
            "quinta",
            "sexta",
            "sabado",
            "domingo",
            "hora_abertura",
            "hora_fechamento",
            "inicio_intervalo",
            "fim_intervalo",
        }
        assert restricoes_unicas == {
            ("id_estabelecimento",),
        }
        assert restricoes_check == {
            "ck_horario_abertura_fechamento",
            "ck_horario_intervalo",
        }
        assert chaves_estrangeiras == {
            (
                ("id_estabelecimento",),
                "estabelecimento",
                ("id_estabelecimento",),
            ),
        }
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()

def test_tabela_servico(tmp_path):
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
            for coluna in inspecao.get_columns("servico")
        }
        # Lista as colunas com restrições de unique na tabela
        restricoes_unicas = {
            tuple(restricao["column_names"])
            for restricao in inspecao.get_unique_constraints("servico")
        }
        # Lista os nomes das restrições de check
        restricoes_check = {
            restricao["name"]
            for restricao in inspecao.get_check_constraints("servico")
        }
        # Lista as chaves estrangeiras da tabela
        chaves_estrangeiras = {
            (
                tuple(chave["constrained_columns"]),
                chave["referred_table"],
                tuple(chave["referred_columns"]),
            )
            for chave in inspecao.get_foreign_keys("servico")
        }
        # Resultado esperado e comparações
        assert colunas == {
            "id_servico",
            "id_estabelecimento",
            "nome",
            "descricao",
            "preco",
            "duracao_minutos",
            "ativo",
        }
        assert restricoes_unicas == set()
        assert restricoes_check == {
            "ck_servico_preco",
            "ck_servico_duracao",
        }
        assert chaves_estrangeiras == {
            (
                ("id_estabelecimento",),
                "estabelecimento",
                ("id_estabelecimento",),
            ),
        }
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()

def test_tabela_agendamento(tmp_path):
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
            for coluna in inspecao.get_columns("agendamento")
        }
        # Lista as colunas com restrições de unique na tabela
        restricoes_unicas = {
            tuple(restricao["column_names"])
            for restricao in inspecao.get_unique_constraints("agendamento")
        }
        # Lista os nomes das restrições de check
        restricoes_check = {
            restricao["name"]
            for restricao in inspecao.get_check_constraints("agendamento")
        }
        # Lista as chaves estrangeiras da tabela
        chaves_estrangeiras = {
            (
                tuple(chave["constrained_columns"]),
                chave["referred_table"],
                tuple(chave["referred_columns"]),
            )
            for chave in inspecao.get_foreign_keys("agendamento")
        }
        # Resultado esperado e comparações
        assert colunas == {
            "id_agendamento",
            "id_servico",
            "nome_cliente",
            "telefone_cliente",
            "data_agendamento",
            "horario_inicio",
            "horario_fim",
            "status",
            "data_cadastro",
            "data_cancelamento",
        }
        assert restricoes_unicas == set()
        assert restricoes_check == {
            "ck_agendamento_horario",
            "ck_agendamento_status",
            "ck_agendamento_data_cancelamento",
        }
        assert chaves_estrangeiras == {
            (
                ("id_servico",),
                "servico",
                ("id_servico",),
            ),
        }
    # Fecha a engine do SQLAlchemy
    finally:
        motor_teste.dispose()

def test_relacionamentos_models():
    # Cria objetos com os relacionamentso de cada model
    relacionamentos_estabelecimento = inspect(Estabelecimento).relationships
    relacionamentos_horario = inspect(HorarioFuncionamento).relationships
    relacionamentos_servico = inspect(Servico).relationships
    relacionamentos_agendamento = inspect(Agendamento).relationships
    # Resultado esperado e comparações
    assert relacionamentos_estabelecimento["horario_funcionamento"].back_populates == "estabelecimento"
    assert relacionamentos_horario["estabelecimento"].back_populates == "horario_funcionamento"
    assert relacionamentos_estabelecimento["servicos"].back_populates == "estabelecimento"
    assert relacionamentos_servico["estabelecimento"].back_populates == "servicos"
    assert relacionamentos_servico["agendamentos"].back_populates == "servico"
    assert relacionamentos_agendamento["servico"].back_populates == "agendamentos"
