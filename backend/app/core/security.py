from pwdlib import PasswordHash

hash_senhas = PasswordHash.recommended()

def gerar_hash_senha(senha: str) -> str:
    return hash_senhas.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return hash_senhas.verify(senha, senha_hash)
