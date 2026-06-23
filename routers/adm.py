import logging
import secrets

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection
from schemas.adm import UpdateClientChargeInput, UpdateClientChargeResponse


router = APIRouter(
    prefix="/adm",
    tags=["Adm"],
    dependencies=[Depends(verify)],
)
logger = logging.getLogger(__name__)

TABLE = "dbo.sinal_financeiro_hiscobranca"
FIELD_MAP = {
    "status": "status",
    "resposta": "resposta",
    "dt_projecao_pgto": "dt_projecao_pgto",
}


@router.patch(
    "/client-charge",
    response_model=UpdateClientChargeResponse,
    operation_id="atualizarCobrancaCliente",
    summary="Atualizar Cobrança de Cliente",
    description="""
Atualiza os campos de cobrança gerenciados via webhook em
`dbo.sinal_financeiro_hiscobranca`, localizando os registros por `contato`.

Somente os campos abaixo podem ser alterados por este endpoint:
- `status`
- `resposta`
- `dt_projecao_pgto`

`dt_cobranca` é preenchida automaticamente pelo backend com a data e hora
atual sempre que a atualização é processada.
""",
    responses={
        200: {"description": "Cobrança atualizada"},
        400: {"description": "Nenhum campo de cobrança informado"},
        403: {"description": "Token inválido ou ausente"},
        404: {"description": "Nenhuma cobrança encontrada para o filtro informado"},
        422: {"description": "Payload inválido"},
        503: {"description": "Falha ao atualizar a cobrança"},
    },
)
def update_client_charge(
    payload: UpdateClientChargeInput = Body(
        ...,
        description="Dados recebidos via webhook para atualizar a cobrança do cliente",
    )
):
    values = payload.dict(exclude_unset=True)
    contato = values.pop("contato").strip()
    changes = {key: value for key, value in values.items() if key in FIELD_MAP}

    assignments = ", ".join(
        [
            "dt_cobranca = CONVERT(datetime2(0), SYSDATETIMEOFFSET() AT TIME ZONE 'E. South America Standard Time')"
        ]
        + [f"{FIELD_MAP[key]} = ?" for key in changes]
    )

    try:
        with get_sqlserver_connection() as conn:
            conn.timeout = 20
            cursor = conn.cursor()
            cursor.execute("SET XACT_ABORT ON")
            cursor.execute(
                f"""
                UPDATE {TABLE} WITH (ROWLOCK)
                SET {assignments}
                WHERE LTRIM(RTRIM(contato)) = ?
                """,
                *changes.values(),
                contato,
            )
            updated_count = cursor.rowcount

        if updated_count < 1:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma cobrança encontrada para o contato informado",
            )
    except HTTPException:
        raise
    except Exception:
        reference = secrets.token_hex(4).upper()
        logger.exception(
            "Client charge update failed: reference=%s contato=%s fields=%s",
            reference,
            contato,
            sorted(changes),
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Não foi possível atualizar a cobrança do cliente",
                "reference": reference,
            },
            headers={"X-Request-Reference": reference},
        )

    return {
        "ok": True,
        "updated_count": updated_count,
        "contato": contato,
    }
