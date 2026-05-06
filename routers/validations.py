from fastapi import APIRouter, Body, Depends
from core.auth import verify
from schemas.validations import ValidateDocumentInput, ValidateDocumentResponse
from services.docvalid import validate_cnpj, validate_cpf


router = APIRouter(
    prefix="/validations",
    tags=["General"],
    dependencies=[Depends(verify)]
)

@router.post(
    "/document",
    response_model=ValidateDocumentResponse,
    operation_id="validarDocumento",
    summary="Validar Documento",
    description="""
Valida CPF ou CNPJ informado na requisição. Regras aplicadas:
- CPF deve conter apenas números.
- CPF deve ter exatamente 11 dígitos.
- CPF não pode conter pontos, traços, letras, espaços ou caracteres especiais.
- CNPJ deve conter apenas letras e números.
- CNPJ deve ter exatamente 14 caracteres.
- CNPJ aceita o novo formato alfanumérico.
- CNPJ não pode conter pontos, barras, traços, espaços ou caracteres especiais.
- Os dois últimos caracteres do CNPJ devem ser números.
- CPF e CNPJ têm os dígitos verificadores validados.
""",
    responses={
        200: {
            "description": "Resultado da validação do documento.",
            "content": {
                "application/json": {
                    "examples": {
                        "cpf_valido": {
                            "summary": "CPF válido",
                            "value": {
                                "ok": True,
                                "documento_original": "12345678909",
                                "documento_valido": True,
                                "tipo_documento": "CPF",
                                "status_documento": "VALID_CPF",
                                "motivo_invalido": ""
                            }
                        },
                        "cpf_formato_invalido": {
                            "summary": "CPF com formato inválido",
                            "value": {
                                "ok": True,
                                "documento_original": "123.456.789-09",
                                "documento_valido": False,
                                "tipo_documento": "CPF",
                                "status_documento": "INVALID_CPF_FORMAT",
                                "motivo_invalido": "CPF deve conter apenas números, sem pontos, traços, letras ou espaços"
                            }
                        },
                        "cpf_quantidade_invalida": {
                            "summary": "CPF com quantidade inválida",
                            "value": {
                                "ok": True,
                                "documento_original": "123456789",
                                "documento_valido": False,
                                "tipo_documento": "CPF",
                                "status_documento": "INVALID_CPF_LENGTH",
                                "motivo_invalido": "CPF deve conter exatamente 11 dígitos"
                            }
                        },
                        "cnpj_valido": {
                            "summary": "CNPJ válido",
                            "value": {
                                "ok": True,
                                "documento_original": "12345678000195",
                                "documento_valido": True,
                                "tipo_documento": "CNPJ",
                                "status_documento": "VALID_CNPJ",
                                "motivo_invalido": ""
                            }
                        },
                        "cnpj_formato_invalido": {
                            "summary": "CNPJ com formato inválido",
                            "value": {
                                "ok": True,
                                "documento_original": "12.345.678/0001-95",
                                "documento_valido": False,
                                "tipo_documento": "CNPJ",
                                "status_documento": "INVALID_CNPJ_FORMAT",
                                "motivo_invalido": "CNPJ deve conter apenas letras e números, sem pontos, barras, traços ou espaços"
                            }
                        }
                    }
                }
            }
        },
        403: {
            "description": "Token inválido ou ausente."
        },
        422: {
            "description": "Payload inválido. Verifique se os campos `tipo` e `valor` foram enviados corretamente."
        }
    }
)
def validate_document(
    payload: ValidateDocumentInput = Body(
        ...,
        description="Dados para validação do documento. Informe o tipo do documento e o valor a ser validado."
    )
):
    tipo = str(payload.tipo or "").strip().lower()
    valor = str(payload.valor or "").strip()

    if tipo == "cpf":
        valid, status, reason = validate_cpf(valor)
        tipo_documento = "CPF"

    elif tipo == "cnpj":
        valid, status, reason = validate_cnpj(valor)
        tipo_documento = "CNPJ"
        valor = valor.upper()

    else:
        valid = False
        status = "INVALID_DOCUMENT_TYPE"
        reason = "Tipo de documento inválido"
        tipo_documento = ""

    return {
        "ok": True,
        "documento_original": valor,
        "documento_valido": valid,
        "tipo_documento": tipo_documento,
        "status_documento": status,
        "motivo_invalido": reason
    }