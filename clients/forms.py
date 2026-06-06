from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "platform", "email", "company", "notes", "first_contact_date", "last_contact_date"]
        widgets = {
            "first_contact_date": forms.DateInput(attrs={"type": "date"}),
            "last_contact_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-neutral-800 dark:bg-neutral-950"
        for field in self.fields.values():
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {base_classes}".strip()
