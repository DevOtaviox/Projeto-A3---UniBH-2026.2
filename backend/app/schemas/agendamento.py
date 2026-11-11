import re
from datetime import date, datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Quantidade máxima de dias à frente que o cliente pode agendar
# Regra fixa de 30 dias nessa primeira versão
LIMITE_DIAS_AGENDAMENTO = 30
# Os horários disponíveis são oferecidos em intervalos de 10 minutos
INTERVALO_MINUTOS = 10


# Cadastro de agendamento feito pelo cliente na página pública
# O cliente não tem conta, então informa apenas nome e telefone
# Campos que NÃO vêm do cliente (preenchidos pelo back-end):
# - horario_fim: calculado com horario_inicio + duracao_minutos do serviço
# - status: começa sempre como "agendado"
# - data_cadastro: preenchida automaticamente pelo model
# - data_cancelamento: só é preenchida quando o agendamento é cancelado
class AgendamentoCriacao(BaseModel):
    id_servico: int = Field(gt=0)
    nome_cliente: str = Field(min_length=1, max_length=150)
    telefone_cliente: str = Field(min_length=10, max_length=20)
    data_agendamento: date
    horario_inicio: time
    # Módulo do pydantic pra validar um campo específico
    # Roda antes de criar o objeto e pode alterar o valor recebido
    @field_validator("telefone_cliente")
    @classmethod
    def validar_telefone(cls, telefone: str) -> str:
        # Remove a máscara, ex: "(31) 99999-9999" vira "31999999999"
        numeros = re.sub(r"[\s()+-]", "", telefone)
        # Valida DDD + número: 10 dígitos (fixo) ou 11 dígitos (celular)
        if not re.fullmatch(r"[0-9]{10,11}", numeros):
            raise ValueError("Telefone deve conter DDD e número, com 10 ou 11 dígitos.")
        # Salva o telefone só com os números
        return numeros
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_agendamento(self):
        hoje = date.today()
        # Lança erro se a data do agendamento já passou
        if self.data_agendamento < hoje:
            raise ValueError("A data do agendamento não pode estar no passado.")
        # Lança erro se a data passar do limite de dias permitido
        if self.data_agendamento > hoje + timedelta(days=LIMITE_DIAS_AGENDAMENTO):
            raise ValueError(
                f"O agendamento pode ser feito com até {LIMITE_DIAS_AGENDAMENTO} dias de antecedência."
            )
        # Lança erro se o horário não estiver em um intervalo de 10 minutos
        # Ex: 10:00, 10:10 e 10:20 são válidos, 10:05 não é
        if (
            self.horario_inicio.minute % INTERVALO_MINUTOS != 0
            or self.horario_inicio.second != 0
            or self.horario_inicio.microsecond != 0
        ):
            raise ValueError(
                f"O horário deve seguir intervalos de {INTERVALO_MINUTOS} minutos."
            )
        # As regras que dependem do banco ficam na camada de services, não no schema:
        # - serviço existe e está ativo
        # - estabelecimento funciona no dia e no horário escolhidos
        # - horário não conflita com outro agendamento nem com o intervalo
        # - horário de hoje que já passou
        return self

# Atualização de agendamento
# Pelos requisitos (RF20 e RF21), a única alteração é o cancelamento pelo proprietário
# Por isso o status só aceita "cancelado"
# O back-end preenche data_cancelamento no momento do cancelamento
class AgendamentoAtualizacao(BaseModel):
    status: Literal["cancelado"]

# Schema de resposta com dados para o front-end
class AgendamentoResposta(BaseModel):
    id_agendamento: int
    id_servico: int
    nome_cliente: str
    telefone_cliente: str
    data_agendamento: date
    horario_inicio: time
    horario_fim: time
    status: str
    data_cadastro: datetime
    data_cancelamento: datetime | None
    # Converte um objeto do SQLAlchemy em um dicionário
    model_config = ConfigDict(from_attributes=True)
