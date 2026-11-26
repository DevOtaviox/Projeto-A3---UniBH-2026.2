
import app.models

from app.db.session import SessaoLocal, motor_banco
from app.db.base import BaseModelos
from app.models.estabelecimento import Estabelecimento
from app.core.security import gerar_hash_senha


# Dados do estabelecimento de teste
EMAIL = "joao@example.com"
SENHA = "Senha123"

# Cria as tabelas caso ainda não existam
BaseModelos.metadata.create_all(bind=motor_banco)

# Abre conexão com o banco real
sessao = SessaoLocal()

try:
    # Verifica se o estabelecimento já existe
    estabelecimento = (
        sessao.query(Estabelecimento)
        .filter_by(email=EMAIL)
        .first()
    )

    if estabelecimento:
        print("Estabelecimento já cadastrado!")
    else:
        estabelecimento = Estabelecimento(
            nome="Barbearia João",
            endereco="Rua das Flores, 100",
            tipo_documento="CPF",
            documento="12345678901",
            identificador="barbearia-joao",
            email=EMAIL,
            senha_hash=gerar_hash_senha(SENHA),
            ativo=True,
        )

        sessao.add(estabelecimento)
        sessao.commit()

        print("Estabelecimento criado com sucesso!")

    print(f"E-mail: {EMAIL}")
    print(f"Senha: {SENHA}")

except Exception:
    sessao.rollback()
    raise

finally:
    sessao.close()
    motor_banco.dispose()
