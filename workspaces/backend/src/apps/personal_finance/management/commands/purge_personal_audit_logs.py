from django.core.management.base import BaseCommand, CommandError

from apps.personal_finance.services import (
    PERSONAL_AUDIT_RETENTION_DAYS,
    purge_personal_audit_logs,
)


class Command(BaseCommand):
    help = "Remove logs de auditoria pessoal antigos conforme politica de retencao."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=PERSONAL_AUDIT_RETENTION_DAYS,
            help="Quantidade de dias para retencao dos logs de auditoria.",
        )

    def handle(self, *args, **options):
        retention_days = options["days"]
        if retention_days <= 0:
            raise CommandError("--days deve ser maior que zero.")

        deleted_count = purge_personal_audit_logs(older_than_days=retention_days)
        self.stdout.write(
            self.style.SUCCESS(
                "Remocao concluida com sucesso. "
                f"Registros removidos: {deleted_count}."
            )
        )
