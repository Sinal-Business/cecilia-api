import json
import logging
import re
import secrets
from typing import Any, Dict, Iterable, Set

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.auth import verify
from core.database import get_sqlserver_connection
from schemas.chatbots import ChatbotPayload, ChatbotRecordResponse


router = APIRouter(
    prefix="/chatbots",
    tags=["Chatbots"],
    dependencies=[Depends(verify)],
)
logger = logging.getLogger(__name__)

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ENDPOINTS = {
    "registrarAtendimento": {
        "table": "dbo.sinal_ceciliachat_atendimentos",
        "summary": "Registrar Atendimento",
        "description": "Registra um atendimento iniciado pela aplicacao de chatbot.",
        "example": {
            "id_cliente": "12345",
            "tags": "NomeCadastrado",
            "dt_interacao": "2026-06-26T14:30:00",
            "bot": "CECILia",
        },
    },
    "registrarContatoInicial": {
        "table": "dbo.sinal_ceciliachat_contatoinicial",
        "summary": "Registrar Contato Inicial",
        "description": "Registra o primeiro contato do cliente na jornada do chatbot.",
        "example": {
            "id_cliente": "12345",
            "motivo": "Financeiro",
            "menu": "Segunda via",
            "dt_interacao": "2026-06-26T14:31:00",
            "bot": "CECILia",
        },
    },
    "registrarInteracao": {
        "table": "dbo.sinal_ceciliachat_interacoes",
        "summary": "Registrar Interacao",
        "description": "Registra uma interacao ocorrida durante o atendimento no chatbot.",
        "example": {
            "id_cliente": 12345,
            "id_interacao": 1,
            "resumo": "Cliente solicitou segunda via do boleto.",
            "dt_interacao": "2026-06-26T14:32:00",
            "bot": "CECILia",
        },
    },
    "registrarAvaliacaoAtendimento": {
        "table": "dbo.sinal_ceciliachat_avaliacoes",
        "summary": "Registrar Avaliacao de Atendimento",
        "description": "Registra a avaliacao enviada pelo cliente ao final do atendimento.",
        "example": {
            "id_cliente": 12345,
            "nota": "5",
            "comentario": "Atendimento rapido.",
            "dt_interacao": "2026-06-26T14:40:00",
            "bot": "CECILia",
        },
    },
    "registrarAtendimentoHumano": {
        "table": "dbo.sinal_ceciliachat_atenhumano",
        "summary": "Registrar Atendimento Humano",
        "description": "Registra o encaminhamento ou atendimento realizado por uma pessoa.",
        "example": {
            "id_cliente": 12345,
            "pr_resumo": "Cliente pediu suporte humano.",
            "tp_atendimento": "Financeiro",
            "dt_interacao": "2026-06-26T14:35:00",
            "bot": "CECILia",
        },
    },
    "registrarContatoFinal": {
        "table": "dbo.sinal_ceciliachat_contatofinal",
        "summary": "Registrar Contato Final",
        "description": "Registra o encerramento do contato e se a demanda foi resolvida.",
        "example": {
            "id_cliente": 12345,
            "pr_resolvidosn": "S",
            "dt_interacao": "2026-06-26T14:45:00",
            "bot": "CECILia",
        },
    },
    "registrarServico": {
        "table": "dbo.sinal_ceciliachat_servicos",
        "summary": "Registrar Servico",
        "description": "Registra o servico solicitado ou executado durante o atendimento.",
        "example": {
            "id_cliente": 12345,
            "servico": "Segunda via de boleto",
            "dt_interacao": "2026-06-26T14:33:00",
            "bot": "CECILia",
        },
    },
}


def split_table_name(table_name: str) -> tuple[str, str]:
    schema, table = table_name.split(".", 1)
    return schema, table


def quote_identifier(identifier: str) -> str:
    if not IDENTIFIER_RE.fullmatch(identifier):
        raise HTTPException(
            status_code=422,
            detail=f"Campo invalido para insercao: {identifier}",
        )
    return f"[{identifier}]"


def normalize_value(value: Any) -> Any:
    encoded = jsonable_encoder(value)
    if isinstance(encoded, (dict, list)):
        return json.dumps(encoded, ensure_ascii=False)
    return encoded


def get_writable_columns(cursor, table_name: str) -> Set[str]:
    schema, table = split_table_name(table_name)
    rows = cursor.execute(
        """
        SELECT c.name
        FROM sys.columns AS c
        INNER JOIN sys.objects AS o
            ON c.object_id = o.object_id
        INNER JOIN sys.schemas AS s
            ON o.schema_id = s.schema_id
        WHERE s.name = ?
          AND o.name = ?
          AND c.is_identity = 0
          AND c.is_computed = 0
        """,
        schema,
        table,
    ).fetchall()
    return {row[0] for row in rows}


def validate_payload(payload: Dict[str, Any], writable_columns: Iterable[str]) -> Dict[str, Any]:
    if not payload:
        raise HTTPException(status_code=400, detail="Payload vazio")

    writable = set(writable_columns)
    invalid_columns = sorted(set(payload) - writable)
    if invalid_columns:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Payload contem campos que nao existem ou nao podem ser preenchidos",
                "fields": invalid_columns,
            },
        )

    return {key: normalize_value(value) for key, value in payload.items()}


def insert_chatbot_record(route_name: str, payload: ChatbotPayload):
    config = ENDPOINTS[route_name]
    table_name = config["table"]

    try:
        with get_sqlserver_connection() as conn:
            conn.timeout = 20
            cursor = conn.cursor()
            writable_columns = get_writable_columns(cursor, table_name)
            values = validate_payload(dict(payload), writable_columns)

            columns_sql = ", ".join(quote_identifier(column) for column in values)
            placeholders = ", ".join("?" for _ in values)
            cursor.execute(
                f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})",
                *values.values(),
            )
            inserted_count = cursor.rowcount

    except HTTPException:
        raise
    except Exception:
        reference = secrets.token_hex(4).upper()
        logger.exception(
            "Chatbot insert failed: reference=%s table=%s route=%s",
            reference,
            table_name,
            route_name,
        )
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "detail": "Nao foi possivel registrar o evento do chatbot",
                "reference": reference,
            },
            headers={"X-Request-Reference": reference},
        )

    return {
        "ok": True,
        "inserted_count": inserted_count,
        "event": config["summary"],
    }


def register_endpoint(route_name: str, config: Dict[str, Any]) -> None:
    def endpoint(
        payload: ChatbotPayload = Body(
            ...,
            description="Dados do evento enviados pela aplicacao de chatbot",
            examples=[config["example"]],
        )
    ):
        return insert_chatbot_record(route_name, payload)

    endpoint.__name__ = route_name
    router.post(
        f"/{route_name}",
        response_model=ChatbotRecordResponse,
        operation_id=route_name,
        summary=config["summary"],
        description=config["description"],
        responses={
            200: {"description": "Registro criado"},
            400: {"description": "Payload vazio"},
            403: {"description": "Token invalido ou ausente"},
            422: {"description": "Payload invalido"},
            503: {"description": "Falha ao registrar o evento"},
        },
    )(endpoint)


for route, endpoint_config in ENDPOINTS.items():
    register_endpoint(route, endpoint_config)
