from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModelos


# Model para a tabela de Estabelecimento no db
class Estabelecimento(BaseModelos):
    # Nome da tabela
    __tablename__ = "estabelecimento"
    # Define documento como CPF ou CNPJ
    # Se tipo_documento = CPF, documento usa 11 caracteres
    # Se tipo_documento = CNPJ, documento usa 14 caracteres
    __table_args__ = (
        CheckConstraint(
            "tipo_documento IN ('CPF', 'CNPJ')",
            name="ck_estabelecimento_tipo_documento"
        ),
        CheckConstraint(
            "(tipo_documento = 'CPF' AND length(documento) = 11) OR "
            "(tipo_documento = 'CNPJ' AND length(documento) = 14)",
            name="ck_estabelecimento_documento"
        ),
    )
    # Colunas
    id_estabelecimento: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    endereco: Mapped[str] = mapped_column(String(300), nullable=False)
    imagem: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tipo_documento: Mapped[str] = mapped_column(
        String(4),
        nullable=False
    )
    documento: Mapped[str] = mapped_column(
        String(14),
        unique=True,
        nullable=False
    )
    identificador: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    senha_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
