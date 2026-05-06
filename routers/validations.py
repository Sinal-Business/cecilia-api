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
Valida CPF ou CNPJ informado na requisição:
- `valid_doc`: booleano indicando se o documento é válido.
- `status`: status técnico da validação.
- `notes`: mensagem pronta para retorno ao usuário. Retorna `null` quando o documento é válido.

### Regras aplicadas
- CPF deve conter apenas números
- CPF deve ter exatamente 11 dígitos
- CPF não pode conter pontos, traços, letras, espaços ou caracteres especiais
- CNPJ deve conter apenas letras e números
- CNPJ deve ter exatamente 14 caracteres
- CNPJ aceita formato alfanumérico
- CNPJ não pode conter pontos, barras, traços, espaços ou caracteres especiais
- Os dois últimos caracteres do CNPJ devem ser números
- CPF e CNPJ têm os dígitos verificadores validados

### Status possíveis
- `CPF_VALID`
- `CPF_INVALID_EMPTY`
- `CPF_INVALID_FORMAT`
- `CPF_INVALID_LENGTH`
- `CPF_INVALID_DIGITS`
- `CNPJ_VALID`
- `CNPJ_INVALID_EMPTY`
- `CNPJ_INVALID_FORMAT`
- `CNPJ_INVALID_LENGTH`
- `CNPJ_INVALID_DIGITS`
- `DOCUMENT_INVALID_TYPE`
""",
    responses={
        200: {
            "description": "Resultado da validação do documento",
            "content": {
                "application/json": {
                    "examples": {
                        "cpf_valido": {
                            "summary": "CPF válido",
                            "value": {
                                "valid_doc": True,
                                "status": "CPF_VALID",
                                "notes": "Obrigada 😊"
                            }
                        },
                        "cpf_formato_invalido": {
                            "summary": "CPF com formato inválido",
                            "value": {
                                "valid_doc": False,
                                "status": "CPF_INVALID_FORMAT",
                                "notes": "Parece que você enviou um CPF com letras, símbolos ou espaços. Por favor, me envie apenas os números 😊"
                            }
                        },
                        "cpf_quantidade_invalida": {
                            "summary": "CPF com quantidade inválida",
                            "value": {
                                "valid_doc": False,
                                "status": "CPF_INVALID_LENGTH",
                                "notes": "O CPF precisa ter exatamente 11 dígitos. Você pode por favor conferir e me mandar novamente? 😊"
                            }
                        },
                        "cnpj_valido": {
                            "summary": "CNPJ válido",
                            "value": {
                                "valid_doc": True,
                                "status": "CNPJ_VALID",
                                "notes": "Obrigada 😊"
                            }
                        },
                        "cnpj_formato_invalido": {
                            "summary": "CNPJ com formato inválido",
                            "value": {
                                "valid_doc": False,
                                "status": "CNPJ_INVALID_FORMAT",
                                "notes": "Parece que você enviou um CNPJ com símbolos, pontuação ou espaços. Por favor, me envie apenas os dígitos 😊"
                            }
                        },
                        "tipo_invalido": {
                            "summary": "Tipo de documento inválido",
                            "value": {
                                "valid_doc": False,
                                "status": "DOCUMENT_INVALID_TYPE",
                                "notes": "Ocorreu um erro na autenticação, por favor envie falar com humano no chat 😊"
                            }
                        }
                    }
                }
            }
        },
        403: {
            "description": "Token inválido ou ausente"
        },
        422: {
            "description": "Payload inválido"
        }
    }
)
def validate_document(
    payload: ValidateDocumentInput = Body(
        ...,
        description="Dados para validação do documento. Informe o tipo do documento e o valor recebido pela aplicação de origem"
    )
):
    tipo = str(payload.tipo or "").strip().lower()
    valor = str(payload.valor or "").strip()

    if tipo == "cpf":
        valid, status, notes = validate_cpf(valor)

    elif tipo == "cnpj":
        valid, status, notes = validate_cnpj(valor)

    else:
        valid = False
        status = "DOCUMENT_INVALID_TYPE"
        notes = "Ocorreu um erro na autenticação, por favor envie falar com humano no chat 😊"

    return {
        "valid_doc": valid,
        "status": status,
        "notes": notes
    }