from django import forms


class ImportUploadForm(forms.Form):
    file = forms.FileField()
    commit = forms.BooleanField(required=False, initial=False, help_text="Save valid rows instead of previewing only.")
