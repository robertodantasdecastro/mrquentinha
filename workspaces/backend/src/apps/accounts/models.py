from django.conf import settings
from django.db import models

from .fields import EncryptedTextField
from .security import hash_sensitive_value
from .validators import normalize_digits, normalize_phone_digits


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


class UserTaskCategory(TimeStampedModel):
    code = models.CharField(max_length=48, unique=True)
    name = models.CharField(max_length=96)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    technical_scope = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class UserTask(TimeStampedModel):
    category = models.ForeignKey(
        UserTaskCategory,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    technical_scope = models.BooleanField(default=False)
    related_module_slug = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["category__code", "code"]

    def __str__(self) -> str:
        return self.code


class UserTaskAssignment(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignments",
    )
    task = models.ForeignKey(
        UserTask,
        on_delete=models.CASCADE,
        related_name="user_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_assignments_granted",
    )

    class Meta:
        ordering = ["user_id", "task__category__code", "task__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "task"],
                name="accounts_usertaskassignment_user_task_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.task.code}"


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
    phone = EncryptedTextField(blank=True)
    phone_hash = models.CharField(max_length=64, blank=True, default="")
    phone_is_whatsapp = models.BooleanField(default=False)
    secondary_phone = EncryptedTextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    cpf = EncryptedTextField(blank=True)
    cpf_hash = models.CharField(max_length=64, blank=True, default="")
    cnpj = EncryptedTextField(blank=True)
    cnpj_hash = models.CharField(max_length=64, blank=True, default="")
    rg = EncryptedTextField(blank=True)
    rg_hash = models.CharField(max_length=64, blank=True, default="")
    occupation = models.CharField(max_length=120, blank=True)
    postal_code = EncryptedTextField(blank=True)
    street = EncryptedTextField(blank=True)
    street_number = EncryptedTextField(blank=True)
    address_complement = EncryptedTextField(blank=True)
    neighborhood = EncryptedTextField(blank=True)
    city = EncryptedTextField(blank=True)
    state = EncryptedTextField(blank=True)
    country = models.CharField(max_length=80, blank=True, default="Brasil")
    document_type = models.CharField(
        max_length=16,
        choices=DocumentType.choices,
        blank=True,
    )
    document_number = EncryptedTextField(blank=True)
    document_number_hash = models.CharField(max_length=64, blank=True, default="")
    document_issuer = EncryptedTextField(blank=True)
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
    email_verified_at = models.DateTimeField(null=True, blank=True)
    email_verification_token_hash = models.CharField(max_length=128, blank=True)
    email_verification_token_created_at = models.DateTimeField(null=True, blank=True)
    email_verification_last_sent_at = models.DateTimeField(null=True, blank=True)
    email_verification_last_client_base_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"profile:{self.user_id}"

    def save(self, *args, **kwargs):
        self.cpf_hash = hash_sensitive_value(normalize_digits(self.cpf))
        self.cnpj_hash = hash_sensitive_value(normalize_digits(self.cnpj))
        self.rg_hash = hash_sensitive_value(normalize_digits(self.rg))
        self.document_number_hash = hash_sensitive_value(
            normalize_digits(self.document_number)
        )
        self.phone_hash = hash_sensitive_value(normalize_phone_digits(self.phone))
        super().save(*args, **kwargs)


class CustomerGovernanceProfile(TimeStampedModel):
    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        UNDER_REVIEW = "UNDER_REVIEW", "Em revisao"
        SUSPENDED = "SUSPENDED", "Suspensa"
        BLOCKED = "BLOCKED", "Bloqueada"

    class KycReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        APPROVED = "APPROVED", "Aprovada"
        REJECTED = "REJECTED", "Rejeitada"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_governance",
    )
    account_status = models.CharField(
        max_length=24,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    account_status_reason = models.TextField(blank=True)
    checkout_blocked = models.BooleanField(default=False)
    checkout_block_reason = models.CharField(max_length=255, blank=True)
    email_login_allowed_dev = models.BooleanField(default=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_accepted_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_in_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_out_at = models.DateTimeField(null=True, blank=True)
    notifications_opt_in_at = models.DateTimeField(null=True, blank=True)
    notifications_opt_out_at = models.DateTimeField(null=True, blank=True)
    lgpd_data_export_last_at = models.DateTimeField(null=True, blank=True)
    lgpd_data_anonymized_at = models.DateTimeField(null=True, blank=True)
    kyc_review_status = models.CharField(
        max_length=16,
        choices=KycReviewStatus.choices,
        default=KycReviewStatus.PENDING,
    )
    kyc_review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_governance_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"customer-governance:{self.user_id}"


class CustomerSupportTicket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        IN_PROGRESS = "IN_PROGRESS", "Em andamento"
        WAITING_CUSTOMER = "WAITING_CUSTOMER", "Aguardando cliente"
        RESOLVED = "RESOLVED", "Resolvido"
        CLOSED = "CLOSED", "Encerrado"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baixa"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "Alta"
        URGENT = "URGENT", "Urgente"

    class Channel(models.TextChoices):
        WEB = "WEB", "Web"
        APP = "APP", "App"
        EMAIL = "EMAIL", "E-mail"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        PHONE = "PHONE", "Telefone"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    subject = models.CharField(max_length=180)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    priority = models.CharField(
        max_length=12,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    channel = models.CharField(
        max_length=12,
        choices=Channel.choices,
        default=Channel.WEB,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_tickets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_support_tickets",
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"support-ticket:{self.id}"


class CustomerSupportMessage(TimeStampedModel):
    class AuthorType(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Cliente"
        AGENT = "AGENT", "Agente"
        SYSTEM = "SYSTEM", "Sistema"

    ticket = models.ForeignKey(
        CustomerSupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
    )
    author_type = models.CharField(
        max_length=12,
        choices=AuthorType.choices,
        default=AuthorType.CUSTOMER,
    )
    message = models.TextField()
    is_internal = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"support-message:{self.id}"


class CustomerLgpdRequest(TimeStampedModel):
    class RequestType(models.TextChoices):
        ACCESS = "ACCESS", "Acesso aos dados"
        CORRECTION = "CORRECTION", "Correcao de dados"
        DELETION = "DELETION", "Eliminacao de dados"
        ANONYMIZATION = "ANONYMIZATION", "Anonimizacao"
        PORTABILITY = "PORTABILITY", "Portabilidade"
        REVOCATION = "REVOCATION", "Revogacao de consentimento"

    class RequestStatus(models.TextChoices):
        OPEN = "OPEN", "Aberta"
        IN_PROGRESS = "IN_PROGRESS", "Em andamento"
        COMPLETED = "COMPLETED", "Concluida"
        REJECTED = "REJECTED", "Rejeitada"

    class RequestChannel(models.TextChoices):
        APP = "APP", "App"
        WEB = "WEB", "Web"
        EMAIL = "EMAIL", "E-mail"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        PHONE = "PHONE", "Telefone"
        IN_PERSON = "IN_PERSON", "Presencial"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lgpd_requests",
    )
    protocol_code = models.CharField(max_length=40, unique=True)
    request_type = models.CharField(max_length=24, choices=RequestType.choices)
    status = models.CharField(
        max_length=16,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
    )
    channel = models.CharField(
        max_length=16,
        choices=RequestChannel.choices,
        default=RequestChannel.WEB,
    )
    requested_by_name = models.CharField(max_length=180, blank=True)
    requested_by_email = models.EmailField(blank=True)
    requested_at = models.DateTimeField()
    due_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lgpd_requests_resolved",
    )

    class Meta:
        ordering = ["-requested_at", "-id"]

    def __str__(self) -> str:
        return f"LGPD<{self.protocol_code}:{self.status}>"
