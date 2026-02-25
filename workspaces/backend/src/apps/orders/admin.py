from django.contrib import admin

from .models import Order, OrderItem, Payment, PaymentIntent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class PaymentIntentInline(admin.TabularInline):
    model = PaymentIntent
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "delivery_date",
        "status",
        "total_amount",
        "customer",
        "order_date",
    ]
    list_filter = ["status", "delivery_date"]
    search_fields = ["id", "customer__username", "customer__email"]
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "method", "status", "amount", "created_at"]
    list_filter = ["method", "status"]
    search_fields = ["id", "order__id", "provider_ref"]
    inlines = [PaymentIntentInline]


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "payment",
        "provider",
        "status",
        "idempotency_key",
        "provider_intent_ref",
        "created_at",
    ]
    list_filter = ["provider", "status"]
    search_fields = ["id", "payment__id", "idempotency_key", "provider_intent_ref"]
