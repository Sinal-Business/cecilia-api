from typing import Optional

from pydantic import BaseModel, Field


class ChatbotPayload(BaseModel):
    bot: str = Field(
        ...,
        description="Nome do bot responsavel pelo atendimento",
        examples=["Cecilia"],
        min_length=1,
        max_length=255,
    )
    contato: Optional[str] = Field(
        None,
        description="Contato do cliente relacionado ao atendimento",
        examples=["+5521999999999"],
        max_length=255,
    )

    class Config:
        extra = "allow"


class ChatbotRecordResponse(BaseModel):
    ok: bool = Field(..., description="Indica se o registro foi processado")
    inserted_count: int = Field(..., description="Quantidade de registros inseridos")
    event: str = Field(..., description="Evento registrado pela aplicacao")
    reference: Optional[str] = Field(
        None,
        description="Referencia de rastreamento retornada em caso de falha",
    )
