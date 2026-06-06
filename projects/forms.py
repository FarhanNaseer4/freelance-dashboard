from django import forms

from payments.models import Payment
from .models import Milestone, Project, ProjectAttachment, TimeLog


class ProjectAttachmentForm(forms.ModelForm):
    class Meta:
        model = ProjectAttachment
        fields = ["title", "file"]


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "client",
            "name",
            "platform",
            "contract_type",
            "project_type",
            "start_date",
            "delivery_date",
            "budget",
            "hourly_rate",
            "expected_hours",
            "billed_hours",
            "status",
            "priority",
            "description",
            "notes",
            "next_action",
            "follow_up_date",
            "tags",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "delivery_date": forms.DateInput(attrs={"type": "date"}),
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-neutral-800 dark:bg-neutral-950"
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_classes}".strip()


class StyledFormMixin:
    def apply_styles(self):
        base_classes = "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-neutral-800 dark:bg-neutral-950"
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_classes}".strip()


class TimeLogForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TimeLog
        fields = ["date", "hours", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class PaymentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "category", "date_received", "payment_method", "status"]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class MilestoneForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ["title", "amount", "due_date", "status", "payment_status", "delivery_notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "delivery_notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
