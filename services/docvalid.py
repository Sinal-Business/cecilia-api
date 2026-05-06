import re


def validate_cpf(value: str):
    cpf = str(value or "").strip()

    if not cpf:
        return False, "INVALID_CPF_EMPTY", "CPF vazio"

    if not re.fullmatch(r"\d+", cpf):
        return False, "INVALID_CPF_FORMAT", "CPF deve conter apenas números, sem pontos, traços, letras ou espaços"

    if len(cpf) != 11:
        return False, "INVALID_CPF_LENGTH", "CPF deve conter exatamente 11 dígitos"

    if cpf == cpf[0] * 11:
        return False, "INVALID_CPF_DIGITS", "CPF inválido"

    def calc_digit(base, factor):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(base, range(factor, 1, -1))
        )

        remainder = (total * 10) % 11

        return 0 if remainder == 10 else remainder

    first_digit = calc_digit(cpf[:9], 10)
    second_digit = calc_digit(cpf[:10], 11)

    if first_digit != int(cpf[9]) or second_digit != int(cpf[10]):
        return False, "INVALID_CPF_DIGITS", "Dígitos verificadores do CPF inválidos"

    return True, "VALID_CPF", ""

def validate_cnpj(value: str):
    cnpj = str(value or "").strip().upper()

    if not cnpj:
        return False, "INVALID_CNPJ_EMPTY", "CNPJ vazio"

    if not re.fullmatch(r"[A-Z0-9]+", cnpj):
        return False, "INVALID_CNPJ_FORMAT", "CNPJ deve conter apenas letras e números, sem pontos, barras, traços ou espaços"

    if len(cnpj) != 14:
        return False, "INVALID_CNPJ_LENGTH", "CNPJ deve conter exatamente 14 caracteres"

    if not re.fullmatch(r"\d{2}", cnpj[-2:]):
        return False, "INVALID_CNPJ_FORMAT", "Os dois últimos caracteres do CNPJ devem ser números"

    if cnpj == cnpj[0] * 14:
        return False, "INVALID_CNPJ_DIGITS", "CNPJ inválido"

    def char_value(char):
        return ord(char) - 48

    def calc_digit(base, weights):
        total = sum(
            char_value(char) * weight
            for char, weight in zip(base, weights)
        )

        remainder = total % 11

        return 0 if remainder < 2 else 11 - remainder

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    first_digit = calc_digit(cnpj[:12], first_weights)
    second_digit = calc_digit(cnpj[:12] + str(first_digit), second_weights)

    if first_digit != int(cnpj[12]) or second_digit != int(cnpj[13]):
        return False, "INVALID_CNPJ_DIGITS", "Dígitos verificadores do CNPJ inválidos"

    return True, "VALID_CNPJ", ""