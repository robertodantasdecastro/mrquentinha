from decimal import Decimal

from rest_framework import serializers

from .models import (
    Account,
    APBill,
    APBillStatus,
    ARReceivable,
    ARReceivableStatus,
    BankStatement,
    CashDirection,
    CashMovement,
    FinancialClose,
    LedgerEntry,
    StatementLine,
)


def _resolve_reference_pair(attrs: dict, instance) -> tuple[str | None, int | None]:
    reference_type = attrs.get(
        "reference_type",
        getattr(instance, "reference_type", None),
    )
    reference_id = attrs.get(
        "reference_id",
        getattr(instance, "reference_id", None),
    )
    return reference_type, reference_id


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class APBillSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    status = serializers.ChoiceField(choices=APBillStatus.choices)

    class Meta:
        model = APBill
        fields = [
            "id",
            "supplier_name",
            "account",
            "amount",
            "due_date",
            "status",
            "paid_at",
            "reference_type",
            "reference_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        reference_type, reference_id = _resolve_reference_pair(attrs, self.instance)

        has_reference_type = bool(reference_type)
        has_reference_id = reference_id is not None

        if has_reference_type != has_reference_id:
            raise serializers.ValidationError(
                "reference_type e reference_id devem ser informados juntos."
            )

        if has_reference_type and has_reference_id:
            queryset = APBill.objects.filter(
                reference_type=reference_type,
                reference_id=reference_id,
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Ja existe AP com a referencia informada."
                )

        return attrs


class ARReceivableSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    status = serializers.ChoiceField(choices=ARReceivableStatus.choices)

    class Meta:
        model = ARReceivable
        fields = [
            "id",
            "customer",
            "account",
            "amount",
            "due_date",
            "status",
            "received_at",
            "reference_type",
            "reference_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        reference_type, reference_id = _resolve_reference_pair(attrs, self.instance)

        has_reference_type = bool(reference_type)
        has_reference_id = reference_id is not None

        if has_reference_type != has_reference_id:
            raise serializers.ValidationError(
                "reference_type e reference_id devem ser informados juntos."
            )

        if has_reference_type and has_reference_id:
            queryset = ARReceivable.objects.filter(
                reference_type=reference_type,
                reference_id=reference_id,
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Ja existe AR com a referencia informada."
                )

        return attrs


class BankStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatement
        fields = [
            "id",
            "period_start",
            "period_end",
            "opening_balance",
            "closing_balance",
            "source",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)

        period_start = attrs.get(
            "period_start", getattr(self.instance, "period_start", None)
        )
        period_end = attrs.get("period_end", getattr(self.instance, "period_end", None))

        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError(
                "period_start deve ser menor ou igual a period_end."
            )

        return attrs


class StatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementLine
        fields = [
            "id",
            "statement",
            "line_date",
            "description",
            "amount",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CashMovementSerializer(serializers.ModelSerializer):
    direction = serializers.ChoiceField(choices=CashDirection.choices)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    class Meta:
        model = CashMovement
        fields = [
            "id",
            "movement_date",
            "direction",
            "amount",
            "account",
            "note",
            "reference_type",
            "reference_id",
            "statement_line",
            "is_reconciled",
            "created_at",
        ]
        read_only_fields = ["id", "statement_line", "is_reconciled", "created_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        reference_type, reference_id = _resolve_reference_pair(attrs, self.instance)

        has_reference_type = bool(reference_type)
        has_reference_id = reference_id is not None

        if has_reference_type != has_reference_id:
            raise serializers.ValidationError(
                "reference_type e reference_id devem ser informados "
                "juntos quando usados."
            )

        return attrs


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "entry_date",
            "entry_type",
            "amount",
            "debit_account",
            "credit_account",
            "reference_type",
            "reference_id",
            "note",
            "created_at",
        ]
        read_only_fields = fields


class FinancialCloseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialClose
        fields = [
            "id",
            "period_start",
            "period_end",
            "closed_at",
            "closed_by",
            "totals_json",
            "created_at",
        ]
        read_only_fields = ["id", "closed_at", "totals_json", "created_at"]

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)

        period_start = attrs.get(
            "period_start", getattr(self.instance, "period_start", None)
        )
        period_end = attrs.get("period_end", getattr(self.instance, "period_end", None))

        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError(
                "period_start deve ser menor ou igual a period_end."
            )

        return attrs


class ReconcileCashMovementSerializer(serializers.Serializer):
    statement_line_id = serializers.IntegerField(min_value=1)
