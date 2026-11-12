import os
from pathlib import Path

from dotenv import load_dotenv

# Aponta para /backend, onde fica o .env
DIR_BACKEND = Path(__file__).resolve().parents[2]

# Carrega o .env
load_dotenv(DIR_BACKEND / ".env")

# Chave para assinar os tokens para auth
SECRET_KEY = os.getenv("SECRET_KEY")

# Impede a inicialização sem cahve
if not SECRET_KEY:
    raise RuntimeError("A variável SECRET_KEY não foi definida.")
if len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("A SECRET_KEY deve possuir pelo menos 32 bytes.")

# Define o algoritmo da assinatura
ALGORITMO_JWT = "HS256"

# Define o tempo de expiração
TEMPO_EXPIRACAO_TOKEN_MINUTOS = 30
