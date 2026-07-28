from typing import Any, Literal, Optional
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


class ValidateNameInput(BaseModel):
    nome: Any = Field(
        None,
        description="Nome a ser validado, exatamente como foi recebido pelo sistema de origem",
        examples=["Maria da Silva"]
    )


class ValidateNameResponse(BaseModel):
    nome_original: str = Field(
        ...,
        description="Valor recebido após a remoção de espaços no início e no final"
    )
    nome_tratado: str = Field(
        ...,
        description="Nome com espaços e capitalização padronizados"
    )
    nome_valido: bool = Field(
        ...,
        description="Indica se o valor atende às regras de validação de nome"
    )
    status_nome: Literal["VALID_NAME", "INVALID_NAME"] = Field(
        ...,
        description="Status técnico da validação do nome"
    )
    motivo_nome_invalido: str = Field(
        ...,
        description="Motivo da rejeição; retorna uma string vazia quando o nome é válido"
    )
