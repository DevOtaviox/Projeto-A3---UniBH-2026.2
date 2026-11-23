from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


# Dados recebidos
class LoginRequisicao(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)

# Resposta com token
class LoginResposta(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

# Alteração de senha do estabelecimento autenticado
# A nova senha segue as mesmas regras de tamanho do cadastro
class AlteracaoSenhaRequisicao(BaseModel):
    senha_atual: str = Field(min_length=1)
    nova_senha: str = Field(min_length=8, max_length=128)
    # Módulo do pydantic pra validar dados
    @model_validator(mode="after")
    def validar_nova_senha(self):
        # Lança erro se a nova senha for igual à atual
        if self.nova_senha == self.senha_atual:
            raise ValueError("A nova senha deve ser diferente da atual.")
        return self
