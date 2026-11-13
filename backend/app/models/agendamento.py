from datetime import date, datetime, time

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModelos


# Model para a tabela de Agendamento no db
class Agendamento(BaseModelos):
    # Nome da tabela
    __tablename__ = "agendamento"
    # Restrições
    __table_args__ = (
        # Valida horário de início anterior ao horário de término
        CheckConstraint(
            "horario_inicio < horario_fim",
            name="ck_agendamento_horario"
        ),
        # Valida estados do agendamento
        CheckConstraint(
            "status IN ('agendado', 'cancelado')",
            name="ck_agendamento_status"
        ),
        # Valida data de cancelamento de acordo com o status
        # Se cancelado, data_cancelamento deve ser preenchida
        # Se agendado, data_cancelamento deve permanecer vazia
        CheckConstraint(
            "(status = 'agendado' AND data_cancelamento IS NULL) OR "
            "(status = 'cancelado' AND data_cancelamento IS NOT NULL)",
            name="ck_agendamento_data_cancelamento"
        ),
    )
    # Colunas
    id_agendamento: Mapped[int] = mapped_column(primary_key=True)
    id_servico: Mapped[int] = mapped_column(
        ForeignKey("servico.id_servico"),
        nullable=False
    )
    nome_cliente: Mapped[str] = mapped_column(String(150), nullable=False)
    telefone_cliente: Mapped[str] = mapped_column(String(20), nullable=False)
    data_agendamento: Mapped[date] = mapped_column(Date, nullable=False)
    horario_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    horario_fim: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="agendado",
        nullable=False
    )
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    data_cancelamento: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    # Relacionamento muitos pra 1 com Servico
    servico: Mapped["Servico"] = relationship(  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
        "Servico",
        back_populates="agendamentos"
    )
