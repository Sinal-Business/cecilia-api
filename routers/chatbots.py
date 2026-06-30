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
from schemas.chatbots import (
    ChatbotBasePayload,
    ChatbotRecordResponse,
    RegistrarAtendimentoHumanoPayload,
    RegistrarAtendimentoPayload,
    RegistrarAvaliacaoAtendimentoPayload,
    RegistrarContatoFinalPayload,
    RegistrarContatoInicialPayload,
    RegistrarInteracaoPayload,
    RegistrarServicoPayload,
)


router = APIRouter(
    prefix="/chatbots",
    tags=["Chatbots"],
    dependencies=[Depends(verify)],
)
logger = logging.getLogger(__name__)

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CLIENT_ID_FIELD = "id_cliente"
BOT_FIELD = "bot"
BACKEND_TIMESTAMP_FIELD = "dt_interacao"
BACKEND_TIMESTAMP_SQL = (
    "CONVERT(datetime2(0), "
    "SYSDATETIMEOFFSET() AT TIME ZONE 'E. South America Standard Time')"
)

ENDPOINTS = {
    "registrarAtendimento": {
        "model": RegistrarAtendimentoPayload,
        "table": "dbo.sinal_ceciliachat_atendimentos",
        "summary": "Registrar Atendimento",
        "description": "Registra o início do atendimento pela aplicação de chatbot.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "tags": "NomeCadastrado",
            "bot": "Cecilia",
        },
    },
    "registrarContatoInicial": {
        "model": RegistrarContatoInicialPayload,
        "table": "dbo.sinal_ceciliachat_contatoinicial",
        "summary": "Registrar Contato Inicial",
        "description": "Registra o primeiro contato do cliente na jornada.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "motivo": "Financeiro",
            "menu": "Segunda via",
            "bot": "Cecilia",
        },
    },
    "registrarInteracao": {
        "model": RegistrarInteracaoPayload,
        "table": "dbo.sinal_ceciliachat_interacoes",
        "summary": "Registrar Interação",
        "description": "Registra uma interação por IA pela aplicação de chatbot.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "id_interacao": 1,
            "resumo": "Cliente solicitou segunda via do boleto.",
            "bot": "Cecilia",
        },
    },
    "registrarAvaliacaoAtendimento": {
        "model": RegistrarAvaliacaoAtendimentoPayload,
        "table": "dbo.sinal_ceciliachat_avaliacoes",
        "summary": "Registrar Avaliação de Atendimento",
        "description": "Registra avaliação de atendimento enviada pelo cliente ao final do atendimento.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "nota": "5",
            "comentario": "Atendimento rápido.",
            "bot": "Cecilia",
        },
    },
    "registrarAtendimentoHumano": {
        "model": RegistrarAtendimentoHumanoPayload,
        "table": "dbo.sinal_ceciliachat_atenhumano",
        "summary": "Registrar Atendimento Humano",
        "description": "Registra o momento em que o cliente é encaminhado para atendimento humano.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "pr_resumo": "Cliente pediu suporte humano.",
            "tp_atendimento": "Financeiro",
            "bot": "Cecilia",
        },
    },
    "registrarContatoFinal": {
        "model": RegistrarContatoFinalPayload,
        "table": "dbo.sinal_ceciliachat_contatofinal",
        "summary": "Registrar Contato Final",
        "description": "Registra o encerramento do atendimento e se a demanda do cliente foi resolvida.",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "pr_resolvidosn": "S",
            "bot": "Cecilia",
        },
    },
    "registrarServico": {
        "model": RegistrarServicoPayload,
        "table": "dbo.sinal_ceciliachat_servicos",
        "summary": "Registrar Serviço",
        "description": "Registra solicitações de serviço durante o atendimento do cliente (e.g. segunda via de boleto, registro de ocorrências).",
        "example": {
            "id_cliente": "10346316758",
            "contato": "+5521999999999",
            "servico": "Segunda via de boleto",
            "bot": "Cecilia",
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


def payload_to_dict(payload: ChatbotBasePayload) -> Dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=True)
    return payload.dict(exclude_unset=True)


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

    id_cliente = payload.get(CLIENT_ID_FIELD)
    if id_cliente is None or str(id_cliente).strip() == "":
        raise HTTPException(status_code=422, detail="id_cliente e obrigatorio")
    payload[CLIENT_ID_FIELD] = str(id_cliente).strip()

    bot = payload.get(BOT_FIELD)
    if bot is None or str(bot).strip() == "":
        raise HTTPException(status_code=422, detail="bot e obrigatorio")

    if BACKEND_TIMESTAMP_FIELD in payload:
        raise HTTPException(
            status_code=422,
            detail=f"{BACKEND_TIMESTAMP_FIELD} e preenchido automaticamente pela aplicacao",
        )

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


def insert_chatbot_record(route_name: str, payload: ChatbotBasePayload):
    config = ENDPOINTS[route_name]
    table_name = config["table"]

    try:
        with get_sqlserver_connection() as conn:
            conn.timeout = 20
            cursor = conn.cursor()
            writable_columns = get_writable_columns(cursor, table_name)
            values = validate_payload(payload_to_dict(payload), writable_columns)

            columns_sql = ", ".join(
                [quote_identifier(column) for column in values]
                + [quote_identifier(BACKEND_TIMESTAMP_FIELD)]
            )
            placeholders = ", ".join(["?" for _ in values] + [BACKEND_TIMESTAMP_SQL])
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
    payload_model = config["model"]

    def endpoint(
        payload: payload_model = Body(
            ...,
            description="Dados do evento enviados pela aplicação de chatbot. Os campos id_cliente e bot são obrigatórios; contato e os dados específicos do evento são opcionais; dt_interacao é preenchido automaticamente pela API.",
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
