from fastapi import APIRouter

router = APIRouter(tags=["Saúde"])


@router.get("/health")
def verificar_saude():
    return {"status": "ok"}
