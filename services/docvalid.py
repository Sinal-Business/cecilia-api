import re


def validate_cpf(value: str):
    cpf = str(value or "").strip()

    if not cpf:
        return (
            False,
            "CPF_INVALID_EMPTY",
            "Não identifiquei o CPF. Por favor, me envie apenas os números 😊"
        )

    if not re.fullmatch(r"\d+", cpf):
        return (
            False,
            "CPF_INVALID_FORMAT",
            "Parece que você enviou um CPF com letras, símbolos ou espaços. Por favor, me envie apenas os números 😊"
        )

    if len(cpf) != 11:
        return (
            False,
            "CPF_INVALID_LENGTH",
            "O CPF precisa ter exatamente 11 dígitos. Você pode por favor conferir e me mandar novamente? 😊"
        )

    if cpf == cpf[0] * 11:
        return (
            False,
            "CPF_INVALID_DIGITS",
            "O CPF informado não parece ser válido. Você pode por favor conferir e me mandar novamente? 😊"
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
            "O CPF informado não parece ser válido. Você pode por favor conferir e me mandar novamente? 😊"
        )

    return True, "CPF_VALID", "Obrigada 😊"


def validate_cnpj(value: str):
    cnpj = str(value or "").strip()

    if not cnpj:
        return (
            False,
            "CNPJ_INVALID_EMPTY",
            "Não identifiquei o CNPJ. Por favor, me envie o documento novamente 😊"
        )

    if not re.fullmatch(r"[A-Za-z0-9]+", cnpj):
        return (
            False,
            "CNPJ_INVALID_FORMAT",
            "Parece que você enviou um CNPJ com símbolos, pontuação ou espaços. Por favor, me envie apenas os dígitos 😊"
        )

    if len(cnpj) != 14:
        return (
            False,
            "CNPJ_INVALID_LENGTH",
            "O CNPJ precisa ter exatamente 14 caracteres. Você pode por favor conferir e me mandar novamente? 😊"
        )

    if not re.fullmatch(r"\d{2}", cnpj[-2:]):
        return (
            False,
            "CNPJ_INVALID_FORMAT",
            "Os dois últimos caracteres do CNPJ precisam ser números. Você pode por favor conferir e me mandar novamente? 😊"
        )

    cnpj_calc = cnpj.upper()

    if cnpj_calc == cnpj_calc[0] * 14:
        return (
            False,
            "CNPJ_INVALID_DIGITS",
            "O CNPJ informado não parece ser válido. Você pode por favor conferir e me mandar novamente? 😊"
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
            "O CNPJ informado não parece ser válido. Você pode por favor conferir e me mandar novamente? 😊"
        )

    return True, "CNPJ_VALID", "Obrigada 😊"