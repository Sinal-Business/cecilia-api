from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatbotRecordResponse(BaseModel):
    ok: bool = Field(..., description="Indica se o registro foi processado")
    inserted_count: int = Field(..., description="Quantidade de registros inseridos")
    event: str = Field(..., description="Evento registrado pela aplicacao")
    reference: Optional[str] = Field(
        None,
        description="Referencia de rastreamento retornada em caso de falha",
    )


ChatbotPayload = Dict[str, Any]
