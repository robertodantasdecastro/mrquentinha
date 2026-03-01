import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.accounts.validators import (
    is_valid_cnpj_document,
    is_valid_cpf_document,
    is_valid_phone_document,
    normalize_phone_digits,
    normalize_postal_code,
    validate_email_value,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("529.982.247-25", True),
        ("111.111.111-11", False),
        ("123.456.789-09", False),
        ("123", False),
    ],
)
def test_is_valid_cpf_document(value, expected):
    assert is_valid_cpf_document(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("40.688.134/0001-61", True),
        ("11.111.111/1111-11", False),
        ("123", False),
    ],
)
def test_is_valid_cnpj_document(value, expected):
    assert is_valid_cnpj_document(value) is expected


@pytest.mark.parametrize(
    ("value", "normalized", "expected"),
    [
        ("+55 (11) 98888-7777", "11988887777", True),
        ("(11) 3333-2222", "1133332222", True),
        ("11111", "11111", False),
    ],
)
def test_phone_helpers(value, normalized, expected):
    assert normalize_phone_digits(value) == normalized
    assert is_valid_phone_document(value) is expected


def test_normalize_postal_code_remove_mascara():
    assert normalize_postal_code("01001-000") == "01001000"


def test_validate_email_value_ok():
    assert validate_email_value("  pessoa@example.com  ") == "pessoa@example.com"


def test_validate_email_value_invalido():
    with pytest.raises(DjangoValidationError):
        validate_email_value("email-invalido")
