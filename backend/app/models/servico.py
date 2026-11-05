from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModelos


# Model para a tabela de Servico no db
class Servico(BaseModelos):
    # Nome da tabela
    __tablename__ = "servico"
    # Restrições
    __table_args__ = (
        # Valida preço maior ou igual a zero
        CheckConstraint(
            "preco >= 0",
            name="ck_servico_preco"
        ),
        # Valida duração maior que zero
        CheckConstraint(
            "duracao_minutos > 0",
            name="ck_servico_duracao"
        ),
    )
    # Colunas
    id_servico: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey("estabelecimento.id_estabelecimento"),
        nullable=False
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    preco: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    duracao_minutos: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    # Relacionamento muitos pra 1 com Estabelecimento
    estabelecimento: Mapped["Estabelecimento"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        "Estabelecimento",
        back_populates="servicos"
    )
