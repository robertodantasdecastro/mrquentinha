from django.db.models import QuerySet

from .models import OCRJob


def list_ocr_jobs() -> QuerySet[OCRJob]:
    return OCRJob.objects.order_by("-created_at", "-id")


def get_ocr_job(job_id: int) -> OCRJob | None:
    return OCRJob.objects.filter(pk=job_id).first()
