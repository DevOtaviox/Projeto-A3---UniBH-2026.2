from app.main import app
from fastapi.testclient import TestClient


def test_endpoint_health():
    # Cria cliente de teste 
    with TestClient(app) as cliente:
        # Consulta o endpoint de saúde
        resposta = cliente.get("/health")
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
    }

def test_documentacao_swagger():
    # Cria cliente de teste
    with TestClient(app) as cliente:
        # Consulta o endpoind de docs
        resposta = cliente.get("/docs")
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert "swagger-ui" in resposta.text.lower()

def test_especificacao_openapi():
    # Cria cliente de teste
    with TestClient(app) as cliente:
        # Consulta a especificação OpenAPI
        resposta = cliente.get("/openapi.json")
    # Converte resposta para dicionário
    dicionario = resposta.json()
    # Resultado esperado e comparações
    assert resposta.status_code == 200
    assert dicionario["info"]["title"] == "API Plataforma de Agendamentos"
    assert dicionario["info"]["version"] == "1.0.0"
    assert "/health" in dicionario["paths"]
    assert "get" in dicionario["paths"]["/health"]
