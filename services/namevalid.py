import re
import unicodedata
from typing import Any, Dict


REQUEST_WORDS = (
    "boleto", "segunda via", "2 via", "2a via", "2ª via", "emitir", "emissao",
    "pagar", "pagamento", "divida", "debito", "saldo", "contrato", "retirar",
    "cessao", "lote", "financiamento", "negociar", "quitar", "atendimento",
    "suporte", "ajuda", "quero", "gostaria", "preciso", "solicito", "consulta",
    "consultar", "cpf", "cnpj", "imovel", "ocorrencia", "problema", "vazamento",
    "infiltracao", "manutencao", "vistoria", "casa", "apt", "apartamento",
)
NAME_CONNECTORS = {"da", "de", "do", "das", "dos", "e"}
NAME_WORD_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’\-]{2,}$")
INVALID_CHARACTER_RE = re.compile(r"[^A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]")
EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
LINK_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
CPF_RE = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
CNPJ_RE = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
SENTENCE_RE = re.compile(
    r"\b(eu|meu|minha|quero|gostaria|preciso|poderia|favor|segunda|via|"
    r"boleto|contrato|saldo|financiamento|lote)\b",
    re.IGNORECASE,
)


def _normalize(value: Any) -> str:
    text = "" if value is None else str(value)
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if not 0x0300 <= ord(char) <= 0x036F
    ).lower().strip()


def validate_name(raw_name: Any) -> Dict[str, Any]:
    """Validate and format a name using the rules from the original Zap."""
    original = "" if raw_name is None else str(raw_name).strip()
    normalized = _normalize(original)
    words = [word.strip() for word in re.split(r"\s+", original) if word.strip()]

    valid_words = all(
        _normalize(word) in NAME_CONNECTORS or bool(NAME_WORD_RE.fullmatch(word))
        for word in words
    )
    has_name_word = any(
        _normalize(word) not in NAME_CONNECTORS and bool(NAME_WORD_RE.fullmatch(word))
        for word in words
    )
    looks_like_sentence = len(words) >= 4 and bool(SENTENCE_RE.search(normalized))

    valid, reason = True, ""
    if not original:
        valid, reason = False, "Nome vazio"
    elif len(original) < 2:
        valid, reason = False, "Nome muito curto"
    elif len(original) > 60:
        valid, reason = False, "Texto muito longo para ser um nome"
    elif re.search(r"\d", original):
        valid, reason = False, "Contém números"
    elif CPF_RE.search(original) or CNPJ_RE.search(original):
        valid, reason = False, "Contém CPF ou CNPJ"
    elif EMAIL_RE.search(original):
        valid, reason = False, "Contém e-mail"
    elif LINK_RE.search(original):
        valid, reason = False, "Contém link"
    elif INVALID_CHARACTER_RE.search(original):
        valid, reason = False, "Contém caracteres inválidos"
    elif any(word in normalized for word in REQUEST_WORDS):
        valid, reason = False, "Parece ser uma solicitação, não um nome"
    elif looks_like_sentence:
        valid, reason = False, "Parece ser uma frase, não um nome"
    elif not valid_words or not has_name_word:
        valid, reason = False, "Não parece ser um nome válido"

    treated = []
    for word in words:
        normalized_word = _normalize(word)
        treated.append(
            normalized_word if normalized_word in NAME_CONNECTORS
            else word[:1].upper() + word[1:].lower()
        )

    return {
        "nome_original": original,
        "nome_tratado": " ".join(treated),
        "nome_valido": valid,
        "status_nome": "VALID_NAME" if valid else "INVALID_NAME",
        "motivo_nome_invalido": reason,
    }
