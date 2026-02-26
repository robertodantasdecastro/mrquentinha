from rest_framework import serializers

from .models import OCRJob
from .services import apply_ocr_job, create_ocr_job


class OCRJobSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OCRJob
        fields = [
            "id",
            "kind",
            "status",
            "image",
            "image_url",
            "raw_text",
            "parsed_json",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "image_url",
            "parsed_json",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        return create_ocr_job(
            kind=validated_data["kind"],
            image=validated_data["image"],
            raw_text=validated_data.get("raw_text"),
        )

    def get_image_url(self, obj: OCRJob) -> str | None:
        if not obj.image:
            return None

        request = self.context.get("request")
        if request is None:
            return obj.image.url

        return request.build_absolute_uri(obj.image.url)


class OCRJobApplySerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(
        choices=["INGREDIENT", "PURCHASE_ITEM", "PURCHASE"]
    )
    target_id = serializers.IntegerField(min_value=1)
    mode = serializers.ChoiceField(choices=["overwrite", "merge"], default="merge")


class OCRJobApplyResultSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    status = serializers.CharField()
    target_type = serializers.CharField()
    target_id = serializers.IntegerField()
    nutrition_fact_id = serializers.IntegerField(required=False)
    saved_image_field = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        raise NotImplementedError


class OCRJobApplyServiceSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(
        choices=["INGREDIENT", "PURCHASE_ITEM", "PURCHASE"]
    )
    target_id = serializers.IntegerField(min_value=1)
    mode = serializers.ChoiceField(choices=["overwrite", "merge"], default="merge")

    def apply(self, *, job_id: int) -> dict:
        validated = self.validated_data
        return apply_ocr_job(
            job_id=job_id,
            target_type=validated["target_type"],
            target_id=validated["target_id"],
            mode=validated["mode"],
        )
