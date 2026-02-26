from decimal import Decimal

from rest_framework import serializers

from .models import (
    PersonalAccount,
    PersonalAccountType,
    PersonalAuditLog,
    PersonalBudget,
    PersonalCategory,
    PersonalDirection,
    PersonalEntry,
    PersonalImportJob,
    PersonalRecurringFrequency,
    PersonalRecurringRule,
)
from .services import normalize_month_ref


class PersonalAccountSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=PersonalAccountType.choices)

    class Meta:
        model = PersonalAccount
        fields = [
            "id",
            "owner",
            "name",
            "type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        request = self.context["request"]
        name = attrs.get("name", getattr(self.instance, "name", "")).strip()

        queryset = PersonalAccount.objects.filter(owner=request.user, name=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Ja existe conta pessoal com este nome para o usuario."
            )

        attrs["name"] = name
        return attrs


class PersonalCategorySerializer(serializers.ModelSerializer):
    direction = serializers.ChoiceField(choices=PersonalDirection.choices)

    class Meta:
        model = PersonalCategory
        fields = [
            "id",
            "owner",
            "name",
            "direction",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        request = self.context["request"]
        name = attrs.get("name", getattr(self.instance, "name", "")).strip()
        direction = attrs.get(
            "direction",
            getattr(self.instance, "direction", PersonalDirection.OUT),
        )

        queryset = PersonalCategory.objects.filter(
            owner=request.user,
            name=name,
            direction=direction,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Ja existe categoria pessoal com este nome e direction para o usuario."
            )

        attrs["name"] = name
        return attrs


class PersonalEntrySerializer(serializers.ModelSerializer):
    direction = serializers.ChoiceField(choices=PersonalDirection.choices)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    class Meta:
        model = PersonalEntry
        fields = [
            "id",
            "owner",
            "account",
            "category",
            "recurring_rule",
            "import_job",
            "direction",
            "amount",
            "entry_date",
            "description",
            "metadata",
            "recurring_event_key",
            "import_hash",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "recurring_rule",
            "import_job",
            "recurring_event_key",
            "import_hash",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        request = self.context["request"]
        account = attrs.get("account", getattr(self.instance, "account", None))
        category = attrs.get("category", getattr(self.instance, "category", None))
        direction = attrs.get(
            "direction",
            getattr(self.instance, "direction", getattr(category, "direction", None)),
        )

        if account is not None and account.owner_id != request.user.id:
            raise serializers.ValidationError("Conta pessoal invalida para o usuario.")

        if category is not None and category.owner_id != request.user.id:
            raise serializers.ValidationError(
                "Categoria pessoal invalida para o usuario."
            )

        if (
            category is not None
            and direction is not None
            and direction != category.direction
        ):
            raise serializers.ValidationError(
                "direction precisa ser igual ao direction da categoria selecionada."
            )

        metadata = attrs.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise serializers.ValidationError("metadata precisa ser um objeto JSON.")

        return attrs


class PersonalRecurringRuleSerializer(serializers.ModelSerializer):
    direction = serializers.ChoiceField(choices=PersonalDirection.choices)
    frequency = serializers.ChoiceField(choices=PersonalRecurringFrequency.choices)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    interval = serializers.IntegerField(min_value=1)

    class Meta:
        model = PersonalRecurringRule
        fields = [
            "id",
            "owner",
            "account",
            "category",
            "direction",
            "amount",
            "description",
            "metadata",
            "frequency",
            "interval",
            "start_date",
            "end_date",
            "next_run_date",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        request = self.context["request"]

        account = attrs.get("account", getattr(self.instance, "account", None))
        category = attrs.get("category", getattr(self.instance, "category", None))
        direction = attrs.get(
            "direction",
            getattr(self.instance, "direction", getattr(category, "direction", None)),
        )

        if account is not None and account.owner_id != request.user.id:
            raise serializers.ValidationError("Conta pessoal invalida para o usuario.")

        if category is not None and category.owner_id != request.user.id:
            raise serializers.ValidationError(
                "Categoria pessoal invalida para o usuario."
            )

        if (
            category is not None
            and direction is not None
            and direction != category.direction
        ):
            raise serializers.ValidationError(
                "direction precisa ser igual ao direction da categoria selecionada."
            )

        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        next_run_date = attrs.get(
            "next_run_date",
            getattr(self.instance, "next_run_date", start_date),
        )

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "start_date deve ser menor ou igual a end_date."
            )

        if start_date and next_run_date and next_run_date < start_date:
            raise serializers.ValidationError(
                "next_run_date deve ser maior ou igual a start_date."
            )

        if end_date and next_run_date and next_run_date > end_date:
            raise serializers.ValidationError(
                "next_run_date nao pode ser maior que end_date."
            )

        metadata = attrs.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise serializers.ValidationError("metadata precisa ser um objeto JSON.")

        return attrs


class PersonalBudgetSerializer(serializers.ModelSerializer):
    limit_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    class Meta:
        model = PersonalBudget
        fields = [
            "id",
            "owner",
            "category",
            "month_ref",
            "limit_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        request = self.context["request"]
        category = attrs.get("category", getattr(self.instance, "category", None))

        if category is not None and category.owner_id != request.user.id:
            raise serializers.ValidationError(
                "Categoria pessoal invalida para o usuario."
            )

        month_ref = attrs.get("month_ref")
        if month_ref is not None:
            normalized_month_ref = normalize_month_ref(month_ref)
            attrs["month_ref"] = normalized_month_ref
        else:
            normalized_month_ref = getattr(self.instance, "month_ref", None)

        if category is not None and normalized_month_ref is not None:
            queryset = PersonalBudget.objects.filter(
                owner=request.user,
                category=category,
                month_ref=normalized_month_ref,
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Ja existe orcamento para a categoria no mes informado."
                )

        return attrs


class PersonalAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalAuditLog
        fields = [
            "id",
            "owner",
            "event_type",
            "resource_type",
            "resource_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class PersonalImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalImportJob
        fields = [
            "id",
            "owner",
            "status",
            "source_filename",
            "delimiter",
            "preview_rows",
            "error_rows",
            "summary",
            "rows_total",
            "rows_valid",
            "rows_invalid",
            "imported_count",
            "skipped_count",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PersonalRecurringMaterializeSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    recurring_rule_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        if attrs["from_date"] > attrs["to_date"]:
            raise serializers.ValidationError(
                "from_date deve ser menor ou igual a to_date."
            )
        return attrs


class PersonalMonthlySummaryQuerySerializer(serializers.Serializer):
    month = serializers.RegexField(regex=r"^\d{4}-\d{2}$")


class PersonalImportPreviewSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    csv_content = serializers.CharField(required=False, allow_blank=False)
    source_filename = serializers.CharField(required=False, allow_blank=True)
    delimiter = serializers.CharField(required=False, default=",", max_length=1)

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        file_obj = attrs.get("file")
        csv_content = attrs.get("csv_content")

        if file_obj is None and not csv_content:
            raise serializers.ValidationError(
                "Informe 'file' (multipart) ou 'csv_content'."
            )

        if file_obj is not None and csv_content:
            raise serializers.ValidationError(
                "Envie apenas um entre 'file' e 'csv_content'."
            )

        delimiter = attrs.get("delimiter", ",")
        if len(delimiter) != 1:
            raise serializers.ValidationError(
                "delimiter deve ter exatamente um caractere."
            )

        return attrs
