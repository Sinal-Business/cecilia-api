from pydantic import BaseModel


class ValidateDocumentInput(BaseModel):
    tipo: str
    valor: str