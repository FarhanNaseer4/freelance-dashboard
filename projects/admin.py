from django.contrib import admin

from payments.models import Payment
from .models import Activity, Milestone, Project, ProjectAttachment, ProjectNote, Tag, TimeLog


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class TimeLogInline(admin.TabularInline):
    model = TimeLog
    extra = 0


class AttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 0


class NoteInline(admin.TabularInline):
    model = ProjectNote
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "client",
        "platform",
        "contract_type",
        "budget",
        "received_amount",
        "remaining_amount",
        "delivery_date",
        "status",
        "priority",
    )
    list_filter = ("platform", "contract_type", "project_type", "status", "priority", "delivery_date")
    search_fields = ("name", "client__name", "description", "notes", "next_action")
    readonly_fields = ("received_amount", "pending_amount", "remaining_amount", "hours_logged", "hourly_earnings", "progress_percent")
    filter_horizontal = ("tags",)
    inlines = [MilestoneInline, PaymentInline, TimeLogInline, AttachmentInline, NoteInline]


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "amount", "due_date", "status", "payment_status")
    list_filter = ("status", "payment_status", "due_date")
    search_fields = ("title", "project__name", "project__client__name")


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ("project", "date", "hours", "earnings")
    list_filter = ("date",)
    search_fields = ("project__name", "description")


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ("project", "title", "uploaded_at")
    search_fields = ("project__name", "title")


@admin.register(ProjectNote)
class ProjectNoteAdmin(admin.ModelAdmin):
    list_display = ("project", "created_at")
    search_fields = ("project__name", "body")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("project", "action", "created_at")
    search_fields = ("project__name", "action", "description")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)
