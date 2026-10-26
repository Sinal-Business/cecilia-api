import logging
import secrets
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection
from schemas.sinal import (
    FinancialCashBulkCreate,
    FinancialCashBulkCreateResponse,
    FinancialCashPage,
    FinancialCashPatch,
    FinancialCashPatchResponse,
)


router = APIRouter(prefix="/sinal", tags=["Sinal"], dependencies=[Depends(verify)])
logger = logging.getLogger(__name__)
TABLE = "dbo.sinal_financeiro_caixa"
MAX_QUERY_PERIOD = timedelta(days=30)

READ_COLUMNS = (
    "lancamento, empresa, filial, co_contabilcod, co_contabil, co_contabilrecla, "
    "cc_analiticocd, cc_analitico, cc_analiticorecla, cc_sinteticonm, fc_codigo, "
    "fc_nome, fc_nomerecla, fc_nomesociedade, dat_emissao, dat_vencimento, "
    "dat_pagamento, dat_ano, dat_periodo, vlr_bruto, vlr_liquido, vlr_titulo, "
    "vlr_pago, vlr_abs, descricao, tip_movimentacao, req_original, req_acumulada, "
    "titulo, pro_codigo, pro_nome, pro_nomerecla, cb_codigo, cb_completa, "
    "cb_completarecla, pag_identificacao, fcx_sintetico, fcx_analitico, "
    "fcx_dretipo, fcx_subgrupo, gpa_reclassif, fcx_variacao, sis_origem, ult_alteracao"
)
CREATE_COLUMNS = tuple(column.strip() for column in READ_COLUMNS.split(",") if column.strip())[1:]
PATCH_COLUMNS = {
    "co_contabilrecla", "cc_analiticorecla", "cc_sinteticonm", "fc_nomerecla",
    "fc_nomesociedade", "req_acumulada", "pro_nomerecla", "cb_completarecla",
    "fcx_analitico", "fcx_dretipo", "fcx_subgrupo", "gpa_reclassif", "fcx_variacao",
}


def _validate_period(start_date: date, end_date: date, label: str):
    if start_date > end_date:
        raise HTTPException(status_code=422, detail=f"{label}_start_date must be <= {label}_end_date")
    if end_date - start_date > MAX_QUERY_PERIOD:
        raise HTTPException(status_code=422, detail=f"{label} date range cannot exceed 31 days")


def _rows_as_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _service_unavailable(operation: str, exc: Exception):
    reference = secrets.token_hex(4).upper()
    logger.exception("Sinal finance operation failed: reference=%s operation=%s", reference, operation)
    return JSONResponse(
        status_code=503,
        content={"detail": "Nao foi possivel processar as movimentacoes financeiras", "reference": reference},
        headers={"X-Request-Reference": reference},
    )


@router.get(
    "/finance/cash-transactions",
    response_model=FinancialCashPage,
    operation_id="listarMovimentacoesFinanceirasCaixa",
    summary="Movimentacoes Financeiras (Caixa)",
    description="Consulta paginada com periodo de pagamento obrigatorio e filtros financeiros opcionais.",
)
def list_financial_cash(
    start_date: date = Query(..., description="Data inicial inclusiva de pagamento"),
    end_date: date = Query(..., description="Data final inclusiva de pagamento; maximo de 31 dias"),
    due_start_date: date | None = Query(None, description="Data inicial inclusiva de vencimento"),
    due_end_date: date | None = Query(None, description="Data final inclusiva de vencimento"),
    empresa: str | None = Query(None, max_length=70),
    filial: str | None = Query(None, max_length=70),
    co_contabilrecla: str | None = Query(None, max_length=255),
    cc_analiticorecla: str | None = Query(None, max_length=100),
    fc_codigo: str | None = Query(None, max_length=15),
    req_original: str | None = Query(None, max_length=6),
    pro_codigo: str | None = Query(None, max_length=100),
    cb_codigo: str | None = Query(None, max_length=10),
    fcx_sintetico: str | None = Query(None, max_length=11),
    fcx_analitico: str | None = Query(None, max_length=20),
    fcx_dretipo: str | None = Query(None, max_length=20),
    fcx_subgrupo: str | None = Query(None, max_length=30),
    fcx_variacao: str | None = Query(None, max_length=27),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=10000),
):
    _validate_period(start_date, end_date, "payment")
    if (due_start_date is None) != (due_end_date is None):
        raise HTTPException(status_code=422, detail="due_start_date and due_end_date must be informed together")
    where = ["dat_pagamento >= ?", "dat_pagamento <= ?"]
    params = [start_date, end_date]
    if due_start_date is not None and due_end_date is not None:
        _validate_period(due_start_date, due_end_date, "due")
        where.extend(["dat_vencimento >= ?", "dat_vencimento <= ?"])
        params.extend([due_start_date, due_end_date])
    filters = {
        "empresa": empresa, "filial": filial, "co_contabilrecla": co_contabilrecla,
        "cc_analiticorecla": cc_analiticorecla, "fc_codigo": fc_codigo,
        "req_original": req_original, "pro_codigo": pro_codigo, "cb_codigo": cb_codigo,
        "fcx_sintetico": fcx_sintetico, "fcx_analitico": fcx_analitico,
        "fcx_dretipo": fcx_dretipo, "fcx_subgrupo": fcx_subgrupo,
        "fcx_variacao": fcx_variacao,
    }
    for column, value in filters.items():
        if value is not None:
            where.append(f"{column} = ?")
            params.append(value.strip())
    sql = f"""
        SELECT {READ_COLUMNS} FROM {TABLE}
        WHERE {' AND '.join(where)}
        ORDER BY dat_pagamento DESC, lancamento DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    try:
        with get_sqlserver_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, *params, offset, limit)
            items = _rows_as_dicts(cursor)
        return {"items": items, "limit": limit, "offset": offset, "count": len(items)}
    except Exception as exc:
        return _service_unavailable("list", exc)


@router.post(
    "/finance/cash-transactions",
    response_model=FinancialCashBulkCreateResponse,
    status_code=201,
    operation_id="criarMovimentacoesFinanceirasCaixa",
    summary="Criar Movimentacoes Financeiras (Caixa)",
    description="Insere de 1 a 500 registros. A API gera lancamentos sequenciais a partir do maior valor existente, sob bloqueio transacional.",
)
def create_financial_cash(payload: FinancialCashBulkCreate = Body(...)):
    records = [item.model_dump() for item in payload.items]
    now = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None, microsecond=0)
    for record in records:
        if record.get("ult_alteracao") is None:
            record["ult_alteracao"] = now
    placeholders = ", ".join("?" for _ in range(len(CREATE_COLUMNS) + 1))
    columns = "lancamento, " + ", ".join(CREATE_COLUMNS)
    try:
        with get_sqlserver_connection() as conn:
            conn.autocommit = False
            cursor = conn.cursor()
            cursor.execute("SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
            cursor.execute("BEGIN TRANSACTION")
            first = cursor.execute(
                f"SELECT ISNULL(MAX(lancamento), 0) + 1 FROM {TABLE} WITH (TABLOCKX, HOLDLOCK)"
            ).fetchone()[0]
            values = [
                tuple([first + index] + [record.get(column) for column in CREATE_COLUMNS])
                for index, record in enumerate(records)
            ]
            cursor.fast_executemany = True
            cursor.executemany(
                f"INSERT INTO {TABLE} ({columns}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
        return {"ok": True, "inserted_count": len(values), "first_lancamento": first, "last_lancamento": first + len(values) - 1}
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        return _service_unavailable("create", exc)


@router.patch(
    "/finance/cash-transactions/{lancamento}",
    response_model=FinancialCashPatchResponse,
    operation_id="atualizarMovimentacaoFinanceiraCaixa",
    summary="Atualizar Movimentacao Financeira (Caixa)",
    description=(
        "Atualiza somente campos de classificacao autorizados. Para alterar valores, datas, empresa, "
        "filial, titulo ou identificadores, solicite a alteracao ao responsavel tecnico. "
        "ult_alteracao e preenchida automaticamente no horario de Brasilia."
    ),
)
def update_financial_cash(lancamento: int, payload: FinancialCashPatch = Body(...)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Informe ao menos um campo autorizado para alteracao")
    unsupported = sorted(set(changes) - PATCH_COLUMNS)
    if unsupported:
        raise HTTPException(
            status_code=422,
            detail=f"Campos nao autorizados: {', '.join(unsupported)}. Solicite a alteracao ao responsavel tecnico.",
        )
    assignments = ", ".join(f"{column} = ?" for column in changes)
    timestamp_sql = "CONVERT(datetime, SYSDATETIMEOFFSET() AT TIME ZONE 'E. South America Standard Time')"
    try:
        with get_sqlserver_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {TABLE} SET {assignments}, ult_alteracao = {timestamp_sql} WHERE lancamento = ?",
                *changes.values(), lancamento,
            )
            if cursor.rowcount != 1:
                raise HTTPException(status_code=404, detail="Lancamento nao encontrado")
            updated_at = cursor.execute(
                f"SELECT ult_alteracao FROM {TABLE} WHERE lancamento = ?", lancamento
            ).fetchone()[0]
        return {"ok": True, "lancamento": lancamento, "updated_fields": list(changes), "ult_alteracao": updated_at}
    except HTTPException:
        raise
    except Exception as exc:
        return _service_unavailable("patch", exc)
