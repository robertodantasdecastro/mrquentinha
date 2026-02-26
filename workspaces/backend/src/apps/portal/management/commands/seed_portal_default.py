from django.core.management.base import BaseCommand

from apps.portal.services import seed_portal_defaults


class Command(BaseCommand):
    help = (
        "Cria/atualiza configuracao default do Portal CMS "
        "(portal + templates web cliente)."
    )

    def handle(self, *args, **options):
        result = seed_portal_defaults()
        self.stdout.write(
            self.style.SUCCESS(
                "Portal CMS default aplicado: "
                f"config_id={result['config_id']} "
                f"config_created={result['config_created']} "
                f"sections_created={result['sections_created']} "
                f"sections_updated={result['sections_updated']}"
            )
        )
