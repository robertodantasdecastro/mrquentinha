from django.db import models


class PortalPage(models.TextChoices):
    HOME = "home", "Home"
    CARDAPIO = "cardapio", "Cardapio"
    SOBRE = "sobre", "Sobre"
    COMO_FUNCIONA = "como-funciona", "Como funciona"
    CONTATO = "contato", "Contato"


class PortalConfig(models.Model):
    SINGLETON_KEY = "default"

    singleton_key = models.CharField(
        max_length=32,
        unique=True,
        default=SINGLETON_KEY,
        editable=False,
    )
    active_template = models.CharField(max_length=64, default="classic")
    available_templates = models.JSONField(default=list, blank=True)
    client_active_template = models.CharField(
        max_length=64,
        default="client-classic",
    )
    client_available_templates = models.JSONField(default=list, blank=True)
    site_name = models.CharField(max_length=120, default="Mr Quentinha")
    site_title = models.CharField(max_length=180, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    primary_color = models.CharField(max_length=32, default="#FF6A00")
    secondary_color = models.CharField(max_length=32, default="#1F2937")
    dark_bg_color = models.CharField(max_length=32, default="#0F172A")
    android_download_url = models.URLField(blank=True, default="")
    ios_download_url = models.URLField(blank=True, default="")
    qr_target_url = models.URLField(blank=True, default="")
    local_hostname = models.CharField(max_length=120, default="mrquentinha")
    local_network_ip = models.CharField(max_length=64, blank=True, default="")
    root_domain = models.CharField(max_length=180, default="mrquentinha.local")
    portal_domain = models.CharField(max_length=180, default="www.mrquentinha.local")
    client_domain = models.CharField(max_length=180, default="app.mrquentinha.local")
    admin_domain = models.CharField(max_length=180, default="admin.mrquentinha.local")
    api_domain = models.CharField(max_length=180, default="api.mrquentinha.local")
    portal_base_url = models.URLField(default="http://mrquentinha:3000")
    client_base_url = models.URLField(default="http://mrquentinha:3001")
    admin_base_url = models.URLField(default="http://mrquentinha:3002")
    backend_base_url = models.URLField(default="http://mrquentinha:8000")
    proxy_base_url = models.URLField(default="http://mrquentinha:8088")
    cors_allowed_origins = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portal config"
        verbose_name_plural = "Portal config"

    def __str__(self) -> str:
        return f"PortalConfig<{self.active_template}>"


class PortalSection(models.Model):
    config = models.ForeignKey(
        PortalConfig,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    template_id = models.CharField(max_length=64, db_index=True)
    page = models.CharField(max_length=40, choices=PortalPage.choices, db_index=True)
    key = models.CharField(max_length=80)
    title = models.CharField(max_length=180, blank=True, default="")
    body_json = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["config", "template_id", "page", "key"],
                name="portal_section_unique_per_template_page",
            )
        ]

    def __str__(self) -> str:
        return f"{self.template_id}:{self.page}:{self.key}"
