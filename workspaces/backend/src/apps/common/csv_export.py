import csv
from collections.abc import Iterable, Sequence

from django.http import HttpResponse


def build_csv_response(
    *,
    filename: str,
    header: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> HttpResponse:
    """Gera um HttpResponse CSV com cabecalho e linhas."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)

    return response
