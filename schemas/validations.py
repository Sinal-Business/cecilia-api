from typing import Literal
from pydantic import BaseModel, Field


class ValidateDocumentInput(BaseModel):
    tipo: Literal["cpf", "cnpj"] = Field(
        ...,
        description="Tipo de documento que será validado. Use 'cpf' para CPF ou 'cnpj' para CNPJ.",
        examples=["cpf"]
    )

    valor: str = Field(
        ...,
        description="Documento a ser validado. Para CPF, envie apenas números. Para CNPJ, envie apenas letras e números, sem pontos, barras, traços ou espaços.",
        examples=["12345678909"]
    )

class ValidateDocumentResponse(BaseModel):
    ok: bool = Field(
        ...,
        description="Indica se a requisição foi processada pela API."
    )

    documento_original: str = Field(
        ...,
        description="Documento recebido pela API após tratamento básico de espaços. Para CNPJ, o valor é retornado em letras maiúsculas."
    )

    documento_valido: bool = Field(
        ...,
        description="Indica se o documento informado é válido."
    )

    tipo_documento: str = Field(
        ...,
        description="Tipo de documento validado: CPF ou CNPJ."
    )

    status_documento: str = Field(
        ...,
        description="Status técnico da validação. Use este campo para identificar o resultado da análise."
    )

    motivo_invalido: str = Field(
        ...,
        description="Motivo pelo qual o documento foi considerado inválido. Retorna vazio quando o documento é válido."
    )