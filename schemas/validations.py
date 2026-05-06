from typing import Literal, Optional
from pydantic import BaseModel, Field


class ValidateDocumentInput(BaseModel):
    tipo: Literal["cpf", "cnpj"] = Field(
        ...,
        description="Tipo de documento que será validado. Use 'cpf' para CPF ou 'cnpj' para CNPJ",
        examples=["cpf"]
    )

    valor: str = Field(
        ...,
        description="Documento a ser validado exatamente como foi recebido pela aplicação de origem",
        examples=["12345678909"]
    )

class ValidateDocumentResponse(BaseModel):
    valid_doc: bool = Field(
        ...,
        description="Indica se o documento informado é válido"
    )

    status: str = Field(
        ...,
        description="Status técnico da validação do documento"
    )

    notes: Optional[str] = Field(
        None,
        description="Mensagem pronta para retorno ao usuário"
    )