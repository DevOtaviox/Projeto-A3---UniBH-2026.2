from fastapi import FastAPI

app = FastAPI(
    title="Sistema de Agendamento",
    description="API para agendamento online de serviços em Vespasiano.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "API do Sistema de Agendamento"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
