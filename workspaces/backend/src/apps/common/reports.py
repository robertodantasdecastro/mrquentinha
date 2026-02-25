from datetime import date

from rest_framework.exceptions import ValidationError as DRFValidationError


def parse_period(*, from_raw: str | None, to_raw: str | None) -> tuple[date, date]:
    if not from_raw or not to_raw:
        raise DRFValidationError(
            {
                "detail": (
                    "Parametros 'from' e 'to' sao obrigatorios no formato YYYY-MM-DD."
                )
            }
        )

    try:
        from_date = date.fromisoformat(from_raw)
        to_date = date.fromisoformat(to_raw)
    except ValueError as exc:
        raise DRFValidationError(
            {"detail": "Formato invalido. Use 'from' e 'to' como YYYY-MM-DD."}
        ) from exc

    if from_date > to_date:
        raise DRFValidationError(
            {"detail": "Parametro 'from' deve ser menor ou igual a 'to'."}
        )

    return from_date, to_date
