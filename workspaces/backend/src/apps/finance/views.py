from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .selectors import (
    list_accounts,
    list_ap_bills,
    list_ar_receivables,
    list_cash_movements,
)
from .serializers import (
    AccountSerializer,
    APBillSerializer,
    ARReceivableSerializer,
    CashMovementSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_accounts()


class APBillViewSet(viewsets.ModelViewSet):
    serializer_class = APBillSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ap_bills()


class ARReceivableViewSet(viewsets.ModelViewSet):
    serializer_class = ARReceivableSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_ar_receivables()


class CashMovementViewSet(viewsets.ModelViewSet):
    serializer_class = CashMovementSerializer
    permission_classes = [AllowAny]  # TODO: aplicar RBAC por perfis financeiros.

    def get_queryset(self):
        return list_cash_movements()
