from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# Dados recebidos
class LoginRequisicao(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)

# Resposta com token
class LoginResposta(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
