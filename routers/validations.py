from fastapi import APIRouter, Depends
from core.auth import verify
from schemas.validations import ValidateDocumentInput
from services.docvalid import validate_cnpj, validate_cpf


router = APIRouter(
    prefix="/validations",
    tags=["Validações"],
    dependencies=[Depends(verify)]
)

@router.post("/document")
def validate_document(payload: ValidateDocumentInput):
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