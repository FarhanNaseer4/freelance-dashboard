from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("project", "amount", "category", "payment_method", "status", "date_received")
    list_filter = ("category", "status", "payment_method", "date_received")
    search_fields = ("project__name", "project__client__name")
