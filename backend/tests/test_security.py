from app.core.security import gerar_hash_senha, verificar_senha


def test_gerar_hash_senha():
    # Define uma senha para gerar hash
    senha = "Senha123"
    # Gera o hash
    senha_hash = gerar_hash_senha(senha)
    # Resultado esperado e comparações
    assert isinstance(senha_hash, str)
    assert senha_hash != senha

def test_verificar_senha_correta():
    # Define uma senha e gera seu hash
    senha = "Senha123"
    senha_hash = gerar_hash_senha(senha)
    # Verifica se senha e hash correspondem
    resultado = verificar_senha(senha, senha_hash)
    # Resultado esperado e comparações
    assert resultado is True

def test_verificar_senha_incorreta():
    # Define uma senha e gera seu hash
    senha = "Senha123"
    senha_hash = gerar_hash_senha(senha)
    # Verifica se senha e hash correspondem
    resultado = verificar_senha("SenhaErrada", senha_hash)
    # Resultado esperado e comparações
    assert resultado is False
