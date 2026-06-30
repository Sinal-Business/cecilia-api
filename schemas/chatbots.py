from typing import Optional, Union

from pydantic import BaseModel, Field


class ChatbotBasePayload(BaseModel):
    id_cliente: Union[str, int] = Field(
        ...,
        description="Identificador do cliente na aplicação de chatbot",
        examples=["12345"],
    )
    bot: str = Field(
        ...,
        description="Nome do bot/interface responsável pelo atendimento",
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
        extra = "forbid"


class RegistrarAtendimentoPayload(ChatbotBasePayload):
    tags: Optional[str] = Field(
        None,
        description="Tags associadas ao atendimento",
        examples=["NomeCadastrado"],
    )


class RegistrarContatoInicialPayload(ChatbotBasePayload):
    motivo: Optional[str] = Field(
        None,
        description="Motivo informado no primeiro contato",
        examples=["Financeiro"],
    )
    menu: Optional[str] = Field(
        None,
        description="Opção de menu selecionada pelo cliente",
        examples=["Segunda via"],
    )


class RegistrarInteracaoPayload(ChatbotBasePayload):
    id_interacao: Optional[Union[int, str]] = Field(
        None,
        description="Identificador da interação na jornada do atendimento",
        examples=[1],
    )
    resumo: Optional[str] = Field(
        None,
        description="Resumo da interação por IA",
        examples=["Cliente solicitou segunda via do boleto."],
    )


class RegistrarAvaliacaoAtendimentoPayload(ChatbotBasePayload):
    nota: Optional[str] = Field(
        None,
        description="Nota da avaliação enviada pelo cliente",
        examples=["5"],
    )
    comentario: Optional[str] = Field(
        None,
        description="Comentário da avaliação enviada pelo cliente",
        examples=["Atendimento rápido."],
    )


class RegistrarAtendimentoHumanoPayload(ChatbotBasePayload):
    pr_resumo: Optional[str] = Field(
        None,
        description="Resumo do encaminhamento para atendimento humano",
        examples=["Cliente pediu suporte humano."],
    )
    tp_atendimento: Optional[str] = Field(
        None,
        description="Tipo de atendimento humano solicitado",
        examples=["Financeiro"],
    )


class RegistrarContatoFinalPayload(ChatbotBasePayload):
    pr_resolvidosn: Optional[str] = Field(
        None,
        description="Indica se a demanda do cliente foi resolvida",
        examples=["S"],
    )


class RegistrarServicoPayload(ChatbotBasePayload):
    servico: Optional[str] = Field(
        None,
        description="Serviço solicitado durante o atendimento",
        examples=["Segunda via de boleto"],
    )


class ChatbotRecordResponse(BaseModel):
    ok: bool = Field(..., description="Indica se o registro foi processado")
    inserted_count: int = Field(..., description="Quantidade de registros inseridos")
    event: str = Field(..., description="Evento registrado pela aplicacao")
    reference: Optional[str] = Field(
        None,
        description="Referencia de rastreamento retornada em caso de falha",
    )
