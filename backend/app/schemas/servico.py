from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Cadastro de serviço
class ServicoCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    duracao_minutos: int = Field(gt=0)

# Atualização de serviço
# Todos os campos usam default=None para que um campo possa ser atualizado sozinho
class ServicoAtualizacao(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    duracao_minutos: int | None = Field(default=None, gt=0)
    ativo: bool | None = None
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_atualizacao(self):
        # Lança erro se a atualização não alterar nenhum campo
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        # Lança erro antes de um campo obrigatório ir pro db com valor None
        for campo in ("nome", "preco", "duracao_minutos", "ativo"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")
        return self

# Schema de resposta com dados para o front-end
class ServicoResposta(BaseModel):
    id_servico: int
    id_estabelecimento: int
    nome: str
    descricao: str | None
    preco: Decimal
    duracao_minutos: int
    ativo: bool
    # Converte um objeto do SQLAlchemy em um dicionário
    model_config = ConfigDict(from_attributes=True)