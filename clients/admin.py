from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "platform", "email", "company", "last_contact_date", "total_revenue")
    list_filter = ("platform", "first_contact_date", "last_contact_date")
    search_fields = ("name", "email", "company", "notes")
    readonly_fields = ("created_at", "updated_at", "total_revenue")
