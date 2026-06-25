import logging
import secrets

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", include_in_schema=False)
def read_root():
    return {"status": "API on air"}

@router.get("/openapi.yaml", include_in_schema=False)
def get_openapi():
    return FileResponse("openapi.yaml")

@router.get("/.well-known/ai-plugin.json", include_in_schema=False)
def serve_ai_plugin():
    return FileResponse(".well-known/ai-plugin.json")


@router.get(
    "/health/db",
    tags=["Health"],
    dependencies=[Depends(verify)],
    operation_id="checarBancoDados",
    summary="Checar Banco de Dados",
    description="Verifica se a API consegue abrir conexão com o banco SQL Server.",
    responses={
        200: {"description": "Conexão com o banco validada"},
        403: {"description": "Token inválido ou ausente"},
        503: {"description": "Falha ao conectar no banco de dados"},
    },
)
def check_database():
    try:
        with get_sqlserver_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        reference = secrets.token_hex(4).upper()
        logger.exception("Database health check failed: reference=%s", reference)
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "detail": "Não foi possível conectar ao banco de dados",
                "reference": reference,
            },
            headers={"X-Request-Reference": reference},
        )

    return {"ok": True}
