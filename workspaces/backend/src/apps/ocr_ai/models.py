from django.db import models


class OCRKind(models.TextChoices):
    LABEL_FRONT = "LABEL_FRONT", "LABEL_FRONT"
    LABEL_BACK = "LABEL_BACK", "LABEL_BACK"
    RECEIPT = "RECEIPT", "RECEIPT"


class OCRJobStatus(models.TextChoices):
    PENDING = "PENDING", "PENDING"
    PROCESSED = "PROCESSED", "PROCESSED"
    APPLIED = "APPLIED", "APPLIED"
    FAILED = "FAILED", "FAILED"


class OCRJob(models.Model):
    kind = models.CharField(max_length=16, choices=OCRKind.choices)
    status = models.CharField(
        max_length=16,
        choices=OCRJobStatus.choices,
        default=OCRJobStatus.PENDING,
    )
    image = models.ImageField(upload_to="ocr/jobs/%Y/%m/%d")
    raw_text = models.TextField(null=True, blank=True)
    parsed_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"OCRJob-{self.id} ({self.kind}/{self.status})"
