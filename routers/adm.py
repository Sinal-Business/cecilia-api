import logging
import re
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
CLIENT_TABLE = "dbo.sinal_comercial_clientes"
RECEIPT_TABLE = "dbo.sinal_financeiro_receita"
FIELD_MAP = {
    "status": "status",
    "resposta": "resposta",
    "dt_projecao_pgto": "dt_projecao_pgto",
}


def normalize_contact(value: str) -> str:
    contact = re.sub(r"\D", "", value or "")
    if not contact:
        raise HTTPException(
            status_code=422,
            detail="Contato deve conter ao menos um numero",
        )
    return contact


def not_found_response(error_code: str, detail: str, contato: str):
    reference = secrets.token_hex(4).upper()
    logger.info(
        "Client charge update not found: reference=%s error_code=%s contato=%s",
        reference,
        error_code,
        contato,
    )
    return JSONResponse(
        status_code=404,
        content={
            "detail": detail,
            "error_code": error_code,
            "reference": reference,
            "contato": contato,
        },
        headers={"X-Request-Reference": reference},
    )


@router.patch(
    "/client-charge",
    response_model=UpdateClientChargeResponse,
    operation_id="atualizarCobrancaCliente",
    summary="Atualizar Cobrança de Cliente",
    description="""
Atualiza os campos de cobrança gerenciados via webhook em
`dbo.sinal_financeiro_hiscobranca`, localizando os registros por `contato`.
O `contato` pode vir com `+`, espaços, hífens ou parênteses; o backend
normaliza o valor para somente números antes da busca.

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
    contato = normalize_contact(values.pop("contato"))
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
            client = cursor.execute(
                f"""
                SELECT TOP (1)
                    id_cliente,
                    cd_cliente,
                    nm_cliente
                FROM {CLIENT_TABLE}
                CROSS APPLY (
                    SELECT NULLIF(
                        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                            LTRIM(RTRIM(nr_contato)),
                            ' ', ''),
                            '(', ''),
                            ')', ''),
                            '-', ''),
                            '.', ''),
                            '+', ''),
                            CHAR(9), ''),
                            CHAR(160), ''),
                        ''
                    ) AS nr_contato_clean
                ) AS cleaned
                WHERE cleaned.nr_contato_clean = ?
                ORDER BY id_cliente
                """,
                contato,
            ).fetchone()

            if not client:
                return not_found_response(
                    "CLIENT_NOT_FOUND",
                    "Nenhum cliente encontrado para o contato informado",
                    contato,
                )

            cursor.execute(
                f"""
                UPDATE charges WITH (ROWLOCK)
                SET {assignments}
                FROM {TABLE} AS charges
                INNER JOIN {RECEIPT_TABLE} AS receipts
                    ON charges.id = CONCAT(
                        receipts.empresa,
                        '$',
                        receipts.cliente,
                        '$',
                        receipts.cc_analitco,
                        '$',
                        receipts.titulo
                    )
                WHERE receipts.cd_cliente = ?
                """,
                *changes.values(),
                client.cd_cliente,
            )
            updated_count = cursor.rowcount

        if updated_count < 1:
            return not_found_response(
                "INVOICE_NOT_FOUND",
                "Cliente encontrado, mas nenhuma cobranca foi encontrada em hiscobranca",
                contato,
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
