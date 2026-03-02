from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class PaymentsWebhookRateThrottle(SimpleRateThrottle):
    scope = "payments_webhook"

    def get_rate(self):
        return str(
            getattr(settings, "PAYMENTS_WEBHOOK_THROTTLE_RATE", "120/min")
        ).strip()

    def get_cache_key(self, request, view):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            identifier = forwarded_for.split(",")[0].strip()
        else:
            identifier = self.get_ident(request)
        if not identifier:
            identifier = "unknown"
        return self.cache_format % {
            "scope": self.scope,
            "ident": identifier,
        }
