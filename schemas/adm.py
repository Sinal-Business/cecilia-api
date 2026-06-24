from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class UpdateClientChargeInput(BaseModel):
    contato: str = Field(
        ...,
        description="Valor usado para localizar a cobrança; aceita + e pontuação, mas será normalizado para números",
        examples=["+5521999999999"],
        min_length=1,
        max_length=40,
    )
    status: str = Field(
        ...,
        description="Novo status da cobrança",
        examples=["Atual (Com Projeção)"],
        min_length=1,
        max_length=255,
    )
    resposta: Optional[str] = Field(
        None,
        description="Resposta ou observação retornada pelo cliente",
        examples=["Cliente informou previsão de pagamento."],
        max_length=2000,
    )
    dt_projecao_pgto: Optional[date] = Field(
        None,
        description="Data projetada de pagamento no formato YYYY-MM-DD",
        examples=["2026-06-30"],
    )


class UpdateClientChargeResponse(BaseModel):
    ok: bool = Field(..., description="Indica se a atualização foi processada")
    updated_count: int = Field(..., description="Quantidade de cobranças atualizadas")
    contato: str = Field(..., description="Contato usado no filtro")
