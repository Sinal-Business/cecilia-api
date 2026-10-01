import logging
import secrets
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection
from schemas.shopping import (
    HotspotAccessPage,
    ParkingAccessPage,
    ParkingPlacesPage,
    PeopleAccessPage,
    ShoppingSalesPage,
)


router = APIRouter(
    prefix="/shopping",
    tags=["Shopping"],
    dependencies=[Depends(verify)],
)
logger = logging.getLogger(__name__)

HOTSPOT_TABLE = "dbo.spro_flows_hotspotaccess"
PARKING_ACCESS_TABLE = "dbo.spro_flows_parkingaccess"
PARKING_PLACES_TABLE = "dbo.spro_flows_parkingplaces"
PEOPLE_TABLE = "dbo.spro_flows_peopleaccess"
SALES_TABLE = "dbo.spro_financeiro_vendas"
MAX_QUERY_PERIOD = timedelta(days=30)


def _rows_as_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _date_where(column: str, start_date: date | None, end_date: date | None):
    if start_date is None or end_date is None:
        raise HTTPException(
            status_code=422,
            detail="start_date and end_date are required",
        )
    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be less than or equal to end_date",
        )
    if end_date - start_date > MAX_QUERY_PERIOD:
        raise HTTPException(
            status_code=422,
            detail="date range cannot exceed 31 days",
        )
    return f" WHERE {column} >= ? AND {column} <= ?", [start_date, end_date]


def _query_page(
    sql: str, params: list, limit: int, offset: int, *, operation: str
):
    stage = "connect"
    try:
        with get_sqlserver_connection() as conn:
            stage = "cursor"
            cursor = conn.cursor()
            stage = "execute"
            cursor.execute(sql, *params, offset, limit)
            stage = "fetch"
            rows = _rows_as_dicts(cursor)
            stage = "close"
        return rows
    except Exception as exc:
        reference = secrets.token_hex(4).upper()
        # Keep the driver diagnostic on the first line: some log viewers hide
        # the traceback. Do not log SQL parameters or authorization headers.
        error = " ".join(str(exc).split())[:2000]
        logger.exception(
            "Shopping query failed: reference=%s operation=%s stage=%s "
            "error_type=%s error=%s limit=%s offset=%s",
            reference, operation, stage, type(exc).__name__, error, limit, offset,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Nao foi possivel consultar os dados do shopping",
                "reference": reference,
            },
            headers={"X-Request-Reference": reference},
        )


def _page(items, limit: int, offset: int):
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}


@router.get(
    "/flows/hotspot-access",
    response_model=HotspotAccessPage,
    operation_id="listarAcessosHotspotShopping",
    summary="Acessos Hotspot de Wi-Fi",
    description=(
        "Apresenta registros de acesso ao Wi-Fi, com informações de data, "
        "localização aproximada e perfil de acesso. Permite filtros por período."
    ),
)
def list_hotspot_access(
    start_date: date = Query(..., description="Data inicial inclusiva"),
    end_date: date = Query(..., description="Data final inclusiva; máximo de 31 dias"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=10000),
):
    where, params = _date_where("dt_acesso", start_date, end_date)
    sql = f"""
        SELECT id, dh_acesso, dt_acesso, hr_acesso, sexo, dt_nascimento,
               tp_aparelho, cep, uf, cidade, bairro, ar_influencia,
               id_lancamento, cpf
        FROM {HOTSPOT_TABLE}
        {where}
        ORDER BY dt_acesso DESC, dh_acesso DESC, id_lancamento DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, params, limit, offset, operation="hotspot_access")
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)


@router.get(
    "/flows/parking-places",
    response_model=ParkingPlacesPage,
    operation_id="listarLocaisEquipamentosEstacionamento",
    summary="Locais Estacionamento",
    description=(
        "Apresenta os locais e tipos associados aos pontos de operação do "
        "estacionamento. Pode ser usado para identificar os locais informados "
        "nos registros de acesso."
    ),
)
def list_parking_places(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1000),
):
    sql = f"""
        SELECT equipamento, lugar, tipo
        FROM {PARKING_PLACES_TABLE}
        ORDER BY equipamento
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, [], limit, offset, operation="parking_places")
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)


def _parking_place(row: dict, prefix: str):
    equipamento = row.pop(f"{prefix}_equipamento", None)
    lugar = row.pop(f"{prefix}_lugar", None)
    tipo = row.pop(f"{prefix}_tipo", None)
    if equipamento is None:
        return None
    return {"equipamento": equipamento, "lugar": lugar, "tipo": tipo}


@router.get(
    "/flows/parking-access",
    response_model=ParkingAccessPage,
    operation_id="listarAcessosEstacionamento",
    summary="Acessos Estacionamento",
    description=(
        "Apresenta movimentações do estacionamento, incluindo entrada, saída, "
        "permanência e informações de pagamento. Quando disponível, cada evento "
        "inclui a identificação do local correspondente."
    ),
)
def list_parking_access(
    start_date: date = Query(..., description="Data inicial inclusiva"),
    end_date: date = Query(..., description="Data final inclusiva; máximo de 31 dias"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=10000),
):
    where, params = _date_where("pa.dt_entrada", start_date, end_date)
    sql = f"""
        SELECT pa.id, pa.tp_acesso, pa.placa, pa.plano, pa.tp_veiculo,
               pa.dh_entrada, pa.dt_entrada, pa.hr_entrada, pa.eq_entrada,
               pe.equipamento AS entrada_equipamento,
               pe.lugar AS entrada_lugar, pe.tipo AS entrada_tipo,
               pa.dh_saida, pa.dt_saida, pa.hr_saida, pa.eq_saida,
               ps.equipamento AS saida_equipamento,
               ps.lugar AS saida_lugar, ps.tipo AS saida_tipo,
               pa.dh_pagamento, pa.dt_pagamento, pa.hr_pagamento, pa.eq_pagamento,
               pp.equipamento AS pagamento_equipamento,
               pp.lugar AS pagamento_lugar, pp.tipo AS pagamento_tipo,
               pa.vl_pagamento, pa.fr_pagamento, pa.bandeira, pa.mi_duracao,
               pa.nm_voucher, pa.dh_voucher, pa.dt_voucher, pa.hr_voucher,
               pa.eq_voucher, pv.equipamento AS voucher_equipamento,
               pv.lugar AS voucher_lugar, pv.tipo AS voucher_tipo
        FROM {PARKING_ACCESS_TABLE} AS pa
        LEFT JOIN {PARKING_PLACES_TABLE} AS pe ON pe.equipamento = pa.eq_entrada
        LEFT JOIN {PARKING_PLACES_TABLE} AS ps ON ps.equipamento = pa.eq_saida
        LEFT JOIN {PARKING_PLACES_TABLE} AS pp ON pp.equipamento = pa.eq_pagamento
        LEFT JOIN {PARKING_PLACES_TABLE} AS pv ON pv.equipamento = pa.eq_voucher
        {where}
        ORDER BY pa.dt_entrada DESC, pa.dh_entrada DESC, pa.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, params, limit, offset, operation="parking_access")
    if isinstance(items, JSONResponse):
        return items
    for item in items:
        item["entrada_local"] = _parking_place(item, "entrada")
        item["saida_local"] = _parking_place(item, "saida")
        item["pagamento_local"] = _parking_place(item, "pagamento")
        item["voucher_local"] = _parking_place(item, "voucher")
    return _page(items, limit, offset)


@router.get(
    "/flows/people-access",
    response_model=PeopleAccessPage,
    operation_id="listarContagemPessoasShopping",
    summary="Acessos de Pessoas",
    description=(
        "Apresenta registros de fluxo de pessoas por data e ponto de entrada, "
        "com informações contextuais disponíveis para o período."
    ),
)
def list_people_access(
    start_date: date = Query(..., description="Data inicial inclusiva"),
    end_date: date = Query(..., description="Data final inclusiva; máximo de 31 dias"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=10000),
):
    where, params = _date_where("dt_acesso", start_date, end_date)
    sql = f"""
        SELECT id, dt_acesso, clima, entrada, pessoas
        FROM {PEOPLE_TABLE}
        {where}
        ORDER BY dt_acesso DESC, entrada, id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, params, limit, offset, operation="people_access")
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)


@router.get(
    "/finance/sales",
    response_model=ShoppingSalesPage,
    operation_id="listarVendasShopping",
    summary="Vendas por Loja",
    description=(
        "Apresenta vendas acumuladas por loja, LUC e data de referencia. "
        "Por padrao, retorna somente snapshots de fechamento mensal para evitar "
        "a soma indevida dos valores acumulados registrados diariamente."
    ),
)
def list_sales(
    start_date: date = Query(..., description="Data inicial inclusiva"),
    end_date: date = Query(..., description="Data final inclusiva; maximo de 31 dias"),
    loja: str | None = Query(None, min_length=1, max_length=255),
    luc: str | None = Query(None, min_length=1, max_length=10),
    categoria: str | None = Query(None, min_length=1, max_length=255),
    segmento: str | None = Query(None, min_length=1, max_length=255),
    classificacao: str | None = Query(None, min_length=1, max_length=255),
    month_end_only: bool = Query(
        True,
        description="Quando true, retorna apenas o ultimo snapshot de cada mes",
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0, le=10000),
):
    where, params = _date_where("dt_referencia", start_date, end_date)
    filters = [
        ("loja", loja),
        ("luc", luc),
        ("categoria", categoria),
        ("segmento", segmento),
        ("classificacao", classificacao),
    ]
    for column, value in filters:
        if value is not None:
            where += f" AND {column} = ?"
            params.append(value.strip())
    if month_end_only:
        where += " AND dt_referencia = EOMONTH(dt_referencia)"

    sql = f"""
        SELECT id, loja, luc, dt_referencia, vl_vendido,
               categoria, segmento, classificacao
        FROM {SALES_TABLE}
        {where}
        ORDER BY dt_referencia DESC, loja, luc, id
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, params, limit, offset, operation="sales")
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)
