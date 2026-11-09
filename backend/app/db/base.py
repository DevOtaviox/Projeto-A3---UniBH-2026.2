from sqlalchemy.orm import DeclarativeBase


# Base para os modelos do SQLAlchemy
# Serve para o SQLAlchemy reconhecer o que é um modelo do db
class BaseModelos(DeclarativeBase):
    pass
