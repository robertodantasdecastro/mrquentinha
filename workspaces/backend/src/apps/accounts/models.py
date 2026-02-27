from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(TimeStampedModel):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class UserRole(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    class Meta:
        ordering = ["user_id", "role__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="accounts_userrole_user_role_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.role.code}"


class UserProfile(TimeStampedModel):
    class DocumentType(models.TextChoices):
        CPF = "CPF", "CPF"
        CNPJ = "CNPJ", "CNPJ"
        RG = "RG", "RG"
        CNH = "CNH", "CNH"
        PASSAPORTE = "PASSAPORTE", "Passaporte"
        OUTRO = "OUTRO", "Outro"

    class BiometricStatus(models.TextChoices):
        NOT_CONFIGURED = "NOT_CONFIGURED", "Nao configurada"
        PENDING_REVIEW = "PENDING_REVIEW", "Aguardando validacao"
        VERIFIED = "VERIFIED", "Validada"
        REJECTED = "REJECTED", "Rejeitada"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=180, blank=True)
    preferred_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    secondary_phone = models.CharField(max_length=32, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, blank=True)
    cnpj = models.CharField(max_length=18, blank=True)
    rg = models.CharField(max_length=32, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=16, blank=True)
    street = models.CharField(max_length=160, blank=True)
    street_number = models.CharField(max_length=32, blank=True)
    address_complement = models.CharField(max_length=120, blank=True)
    neighborhood = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True, default="Brasil")
    document_type = models.CharField(
        max_length=16,
        choices=DocumentType.choices,
        blank=True,
    )
    document_number = models.CharField(max_length=64, blank=True)
    document_issuer = models.CharField(max_length=120, blank=True)
    profile_photo = models.ImageField(
        upload_to="accounts/profile/%Y/%m/%d",
        blank=True,
        null=True,
    )
    document_front_image = models.ImageField(
        upload_to="accounts/documents/front/%Y/%m/%d",
        blank=True,
        null=True,
    )
    document_back_image = models.ImageField(
        upload_to="accounts/documents/back/%Y/%m/%d",
        blank=True,
        null=True,
    )
    document_selfie_image = models.ImageField(
        upload_to="accounts/documents/selfie/%Y/%m/%d",
        blank=True,
        null=True,
    )
    biometric_photo = models.ImageField(
        upload_to="accounts/biometric/%Y/%m/%d",
        blank=True,
        null=True,
    )
    biometric_status = models.CharField(
        max_length=24,
        choices=BiometricStatus.choices,
        default=BiometricStatus.NOT_CONFIGURED,
    )
    biometric_captured_at = models.DateTimeField(null=True, blank=True)
    biometric_verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"profile:{self.user_id}"
