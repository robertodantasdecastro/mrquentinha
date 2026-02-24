from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .selectors import list_ocr_jobs
from .serializers import (
    OCRJobApplyResultSerializer,
    OCRJobApplyServiceSerializer,
    OCRJobSerializer,
)


class OCRJobViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OCRJobSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [AllowAny]  # TODO: aplicar RBAC (COZINHA/COMPRAS/Admin).

    def get_queryset(self):
        return list_ocr_jobs()

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        input_serializer = OCRJobApplyServiceSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            result = input_serializer.apply(job_id=int(pk))
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.messages) from exc

        output_serializer = OCRJobApplyResultSerializer(data=result)
        output_serializer.is_valid(raise_exception=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)
