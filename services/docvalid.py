import re


def validate_cpf(value: str):
    cpf = str(value or "").strip()

    if not cpf:
        return (
            False,
            "CPF_INVALID_EMPTY",
            "Não identifiquei o CPF informado. Por favor, envie apenas os números do seu CPF."
        )

    if not re.fullmatch(r"\d+", cpf):
        return (
            False,
            "CPF_INVALID_FORMAT",
            "Parece que você enviou um CPF com caracteres especiais, letras ou espaços. Por favor, envie apenas os números do seu CPF."
        )

    if len(cpf) != 11:
        return (
            False,
            "CPF_INVALID_LENGTH",
            "O CPF precisa ter exatamente 11 dígitos. Por favor, confira e envie novamente apenas os números."
        )

    if cpf == cpf[0] * 11:
        return (
            False,
            "CPF_INVALID_DIGITS",
            "O CPF informado não parece ser válido. Por favor, confira os números e envie novamente."
        )

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
        return (
            False,
            "CPF_INVALID_DIGITS",
            "O CPF informado não parece ser válido. Por favor, confira os números e envie novamente."
        )

    return True, "CPF_VALID", None


def validate_cnpj(value: str):
    cnpj = str(value or "").strip()

    if not cnpj:
        return (
            False,
            "CNPJ_INVALID_EMPTY",
            "Não identifiquei o CNPJ informado. Por favor, envie o CNPJ novamente."
        )

    if not re.fullmatch(r"[A-Za-z0-9]+", cnpj):
        return (
            False,
            "CNPJ_INVALID_FORMAT",
            "Parece que você enviou um CNPJ com caracteres especiais, pontuação ou espaços. Por favor, envie apenas letras e números."
        )

    if len(cnpj) != 14:
        return (
            False,
            "CNPJ_INVALID_LENGTH",
            "O CNPJ precisa ter exatamente 14 caracteres. Por favor, confira e envie novamente."
        )

    if not re.fullmatch(r"\d{2}", cnpj[-2:]):
        return (
            False,
            "CNPJ_INVALID_FORMAT",
            "Os dois últimos caracteres do CNPJ precisam ser números. Por favor, confira e envie novamente."
        )

    cnpj_calc = cnpj.upper()

    if cnpj_calc == cnpj_calc[0] * 14:
        return (
            False,
            "CNPJ_INVALID_DIGITS",
            "O CNPJ informado não parece ser válido. Por favor, confira os caracteres e envie novamente."
        )

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

    first_digit = calc_digit(cnpj_calc[:12], first_weights)
    second_digit = calc_digit(cnpj_calc[:12] + str(first_digit), second_weights)

    if first_digit != int(cnpj_calc[12]) or second_digit != int(cnpj_calc[13]):
        return (
            False,
            "CNPJ_INVALID_DIGITS",
            "O CNPJ informado não parece ser válido. Por favor, confira os caracteres e envie novamente."
        )

    return True, "CNPJ_VALID", None