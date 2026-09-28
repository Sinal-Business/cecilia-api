import logging
import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection
from schemas.shopping import (
    HotspotAccessPage,
    ParkingAccessPage,
    ParkingPlacesPage,
    PeopleAccessPage,
)


router = APIRouter(
    prefix="/shopping/flows",
    tags=["Shopping"],
    dependencies=[Depends(verify)],
)
logger = logging.getLogger(__name__)

HOTSPOT_TABLE = "dbo.spro_flows_hotspotaccess"
PARKING_ACCESS_TABLE = "dbo.spro_flows_parkingaccess"
PARKING_PLACES_TABLE = "dbo.spro_flows_parkingplaces"
PEOPLE_TABLE = "dbo.spro_flows_peopleaccess"


def _rows_as_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _date_where(column: str, start_date: date | None, end_date: date | None):
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be less than or equal to end_date",
        )
    clauses = []
    params = []
    if start_date is not None:
        clauses.append(f"{column} >= ?")
        params.append(start_date)
    if end_date is not None:
        clauses.append(f"{column} <= ?")
        params.append(end_date)
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


def _query_page(sql: str, params: list, limit: int, offset: int):
    try:
        with get_sqlserver_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, *params, offset, limit)
            return _rows_as_dicts(cursor)
    except Exception:
        reference = secrets.token_hex(4).upper()
        logger.exception("Shopping flows query failed: reference=%s", reference)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Nao foi possivel consultar os dados de fluxo do shopping",
                "reference": reference,
            },
            headers={"X-Request-Reference": reference},
        )


def _page(items, limit: int, offset: int):
    return {"items": items, "limit": limit, "offset": offset, "count": len(items)}


@router.get(
    "/hotspot-access",
    response_model=HotspotAccessPage,
    operation_id="listarAcessosHotspotShopping",
    summary="Acessos Hotspot de Wi-Fi",
    description=(
        "Apresenta registros de acesso ao Wi-Fi, com informações de data, "
        "localização aproximada e perfil de acesso. Permite filtros por período."
    ),
)
def list_hotspot_access(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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
    items = _query_page(sql, params, limit, offset)
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)


@router.get(
    "/parking-places",
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
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    sql = f"""
        SELECT equipamento, lugar, tipo
        FROM {PARKING_PLACES_TABLE}
        ORDER BY equipamento
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, [], limit, offset)
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)


def _parking_place(row: dict, prefix: str):
    equipamento = row.pop(f"{prefix}_equipamento", None)
    lugar = row.pop(f"{prefix}_lugar", None)
    tipo = row.pop(f"{prefix}_tipo", None)
    if equipamento is None:
        return None
    return {"equipamento": equipamento, "lugar": lugar, "tipo": tipo}


@router.get(
    "/parking-access",
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
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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
    items = _query_page(sql, params, limit, offset)
    if isinstance(items, JSONResponse):
        return items
    for item in items:
        item["entrada_local"] = _parking_place(item, "entrada")
        item["saida_local"] = _parking_place(item, "saida")
        item["pagamento_local"] = _parking_place(item, "pagamento")
        item["voucher_local"] = _parking_place(item, "voucher")
    return _page(items, limit, offset)


@router.get(
    "/people-access",
    response_model=PeopleAccessPage,
    operation_id="listarContagemPessoasShopping",
    summary="Acessos de Pessoas",
    description=(
        "Apresenta registros de fluxo de pessoas por data e ponto de entrada, "
        "com informações contextuais disponíveis para o período."
    ),
)
def list_people_access(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    where, params = _date_where("dt_acesso", start_date, end_date)
    sql = f"""
        SELECT id, dt_acesso, clima, entrada, pessoas
        FROM {PEOPLE_TABLE}
        {where}
        ORDER BY dt_acesso DESC, entrada, id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = _query_page(sql, params, limit, offset)
    return items if isinstance(items, JSONResponse) else _page(items, limit, offset)
