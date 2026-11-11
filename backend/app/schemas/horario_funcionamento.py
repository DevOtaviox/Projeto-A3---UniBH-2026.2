from datetime import time

from pydantic import BaseModel, ConfigDict, model_validator


# Cadastro de horário de funcionamento
class HorarioFuncionamentoCriacao(BaseModel):
    segunda: bool = False
    terca: bool = False
    quarta: bool = False
    quinta: bool = False
    sexta: bool = False
    sabado: bool = False
    domingo: bool = False
    hora_abertura: time
    hora_fechamento: time
    inicio_intervalo: time | None = None
    fim_intervalo: time | None = None
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_horario(self):
        # Lança erro se nenhum dia de funcionamento for selecionado
        dias = (
            self.segunda,
            self.terca,
            self.quarta,
            self.quinta,
            self.sexta,
            self.sabado,
            self.domingo,
        )
        if not any(dias):
            raise ValueError("Selecione ao menos um dia de funcionamento.")
        # Lança erro se horário de abertura for após fechamento
        if self.hora_abertura >= self.hora_fechamento:
            raise ValueError("A abertura deve ser anterior ao fechamento.")
        # Lança erro se apenas um dos horários do intervalo for preenchido
        if (self.inicio_intervalo is None) != (self.fim_intervalo is None):
            raise ValueError("Informe os dois horários do intervalo.")
        # Valida se o intervalo está dentro do funcionamento
        if (
            self.inicio_intervalo is not None
            and self.fim_intervalo is not None
        ) and not (
            self.hora_abertura <= self.inicio_intervalo
            < self.fim_intervalo <= self.hora_fechamento
        ):
            raise ValueError("O intervalo deve estar dentro do funcionamento.")
        return self

# Atualização de horário de funcionamento
# Todos os campos usam default=None para permitir atualização individual
class HorarioFuncionamentoAtualizacao(BaseModel):
    segunda: bool | None = None
    terca: bool | None = None
    quarta: bool | None = None
    quinta: bool | None = None
    sexta: bool | None = None
    sabado: bool | None = None
    domingo: bool | None = None
    hora_abertura: time | None = None
    hora_fechamento: time | None = None
    inicio_intervalo: time | None = None
    fim_intervalo: time | None = None
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_atualizacao(self):
        # Lança erro se a atualização não alterar nenhum campo
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        # Lança erro se um campo obrigatório for preenchido como None
        campos_obrigatorios = (
            "segunda",
            "terca",
            "quarta",
            "quinta",
            "sexta",
            "sabado",
            "domingo",
            "hora_abertura",
            "hora_fechamento",
        )
        for campo in campos_obrigatorios:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")
        # Lança erro se só um horário de intervalo for definido como None
        if (
            self.inicio_intervalo is None
            and "inicio_intervalo" in self.model_fields_set
        ) != (
            self.fim_intervalo is None
            and "fim_intervalo" in self.model_fields_set
        ):
            raise ValueError("Informe os dois horários para remover o intervalo.")
        # Valida se fim do intervalo acontece depois do início se ambos forem informados
        if (
            self.inicio_intervalo is not None
            and self.fim_intervalo is not None
        ) and self.inicio_intervalo >= self.fim_intervalo:
            raise ValueError("O início do intervalo deve ser anterior ao fim.")

        return self

# Schema de resposta com dados para o front-end
class HorarioFuncionamentoResposta(BaseModel):
    id_horario: int
    id_estabelecimento: int
    segunda: bool
    terca: bool
    quarta: bool
    quinta: bool
    sexta: bool
    sabado: bool
    domingo: bool
    hora_abertura: time
    hora_fechamento: time
    inicio_intervalo: time | None
    fim_intervalo: time | None
    # Converte um objeto do SQLAlchemy em um dicionário
    model_config = ConfigDict(from_attributes=True)
