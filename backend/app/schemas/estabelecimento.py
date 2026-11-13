import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# Cadastro de estabelecimento
class EstabelecimentoCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    endereco: str = Field(min_length=1, max_length=300)
    imagem: str | None = Field(default=None, max_length=500)
    tipo_documento: Literal["CPF", "CNPJ"]
    documento: str = Field(min_length=11, max_length=14)
    identificador: str = Field(min_length=1, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_documento(self):
        # Valida CPF com 11 números
        if self.tipo_documento == "CPF":
            if not re.fullmatch(r"[0-9]{11}", self.documento):
                raise ValueError("CPF deve conter 11 números.")
        # Valida CNPJ com 12 caracteres + 2 números
        elif self.tipo_documento == "CNPJ":  # noqa: SIM102
            if not re.fullmatch(r"[A-Za-z0-9]{12}[0-9]{2}", self.documento):
                raise ValueError("CNPJ deve conter 12 caracteres alfanuméricos e 2 números.")
        return self

# Atualização de estabelecimento
# Todos os campos usam default=None para permitir atualização individual
class EstabelecimentoAtualizacao(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    endereco: str | None = Field(default=None, min_length=1, max_length=300)
    imagem: str | None = Field(default=None, max_length=500)
    tipo_documento: Literal["CPF", "CNPJ"] | None = None
    documento: str | None = Field(default=None, min_length=11, max_length=14)
    identificador: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    senha: str | None = Field(default=None, min_length=8, max_length=128)
    ativo: bool | None = None
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_atualizacao(self):
        # Lança erro se a atualização não alterar nenhum campo
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        # Lança erro se um campo obrigatório for preenchido como None
        campos_obrigatorios = (
            "nome",
            "endereco",
            "tipo_documento",
            "documento",
            "identificador",
            "email",
            "senha",
            "ativo",
        )
        for campo in campos_obrigatorios:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")
        # Lança erro se apenas um dos campos do documento for informado
        if (
            ("tipo_documento" in self.model_fields_set)
            != ("documento" in self.model_fields_set)
        ):
            raise ValueError("Informe o tipo e o número do documento juntos.")
        # Verifica se tipo_documento e documento estão sendo atualizados
        if (
            self.tipo_documento is not None
            and self.documento is not None
        ):
            # Valida CPF com 11 números
            if self.tipo_documento == "CPF":
                if not re.fullmatch(r"[0-9]{11}", self.documento):
                    raise ValueError("CPF deve conter exatamente 11 números.")
            # Valida CNPJ com 12 caracteres + 2 números
            elif not re.fullmatch(r"[A-Za-z0-9]{12}[0-9]{2}", self.documento):
                raise ValueError("CNPJ deve conter 12 caracteres alfanuméricos e 2 números.")
        return self

# Schema de resposta com dados para o front-end
class EstabelecimentoResposta(BaseModel):
    id_estabelecimento: int
    nome: str
    endereco: str
    imagem: str | None
    tipo_documento: str
    documento: str
    identificador: str
    ativo: bool
    email: EmailStr
    # Converte um objeto do SQLAlchemy em um dicionário
    model_config = ConfigDict(from_attributes=True)
