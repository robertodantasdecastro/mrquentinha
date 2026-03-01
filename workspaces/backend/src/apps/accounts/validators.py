from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email as django_validate_email


def normalize_digits(value: str) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def normalize_postal_code(value: str) -> str:
    return normalize_digits(value)


def _all_same_digits(value: str) -> bool:
    return bool(value) and len(set(value)) == 1


def is_valid_cpf_document(value: str) -> bool:
    digits = normalize_digits(value)
    if len(digits) != 11 or _all_same_digits(digits):
        return False
    if digits == "12345678909":
        return False

    total = 0
    for index in range(9):
        total += int(digits[index]) * (10 - index)
    check_digit_1 = (total * 10) % 11
    if check_digit_1 == 10:
        check_digit_1 = 0
    if check_digit_1 != int(digits[9]):
        return False

    total = 0
    for index in range(10):
        total += int(digits[index]) * (11 - index)
    check_digit_2 = (total * 10) % 11
    if check_digit_2 == 10:
        check_digit_2 = 0

    return check_digit_2 == int(digits[10])


def is_valid_cnpj_document(value: str) -> bool:
    digits = normalize_digits(value)
    if len(digits) != 14 or _all_same_digits(digits):
        return False

    def _calc_digit(base: str, weights: list[int]) -> int:
        total = sum(int(base[index]) * weights[index] for index in range(len(weights)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    base_twelve = digits[:12]
    first_digit = _calc_digit(base_twelve, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = _calc_digit(
        f"{base_twelve}{first_digit}",
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    )

    return digits == f"{base_twelve}{first_digit}{second_digit}"


def normalize_phone_digits(value: str) -> str:
    digits = normalize_digits(value)

    # Aceita prefixo internacional do Brasil (+55) e normaliza para DDD + numero.
    if digits.startswith("55") and len(digits) in {12, 13}:
        digits = digits[2:]

    return digits


def is_valid_phone_document(value: str) -> bool:
    digits = normalize_phone_digits(value)
    if len(digits) not in {10, 11}:
        return False
    if _all_same_digits(digits):
        return False
    return True


def validate_email_value(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""

    try:
        django_validate_email(normalized)
    except DjangoValidationError as exc:
        raise DjangoValidationError("Email invalido.") from exc

    return normalized
