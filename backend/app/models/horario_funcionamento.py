from datetime import time

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModelos


# Model para a tabela de HorarioFuncionamento no db
class HorarioFuncionamento(BaseModelos):
    # Nome da tabela
    __tablename__ = "horario_funcionamento"

    # Restrições
    __table_args__ = (
        # Valida abertura antes de fechamento
        CheckConstraint(
            "hora_abertura < hora_fechamento",
            name="ck_horario_abertura_fechamento"
        ),
        # Valida horário de almoço
        # Se um dos horários for preenchido (início ou fim) o outro deve ser preenchido também
        # Horário de almoço tem que estar dentro do horário de funcionamento
        CheckConstraint(
            "(inicio_intervalo IS NULL AND fim_intervalo IS NULL) OR "
            "(inicio_intervalo IS NOT NULL AND fim_intervalo IS NOT NULL "
            "AND hora_abertura <= inicio_intervalo "
            "AND inicio_intervalo < fim_intervalo "
            "AND fim_intervalo <= hora_fechamento)",
            name="ck_horario_intervalo"
        ),
    )
    # Colunas
    id_horario: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey("estabelecimento.id_estabelecimento"),
        unique=True,
        nullable=False
    )
    # Define dias de funcionamento
    segunda: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    terca: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    quarta: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    quinta: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    sexta: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    sabado: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    domingo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    # Horários pra funcionamento
    hora_abertura: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fechamento: Mapped[time] = mapped_column(Time, nullable=False)
    inicio_intervalo: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )
    fim_intervalo: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )
    # Relacionamento um pra um com Estabelecimento
    estabelecimento: Mapped["Estabelecimento"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        "Estabelecimento",
        back_populates="horario_funcionamento"
    )
