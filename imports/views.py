import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render

from core.auth import dashboard_login_required
from clients.models import Client
from payments.models import Payment
from projects.models import Activity, Milestone, Project, ProjectAttachment, ProjectNote, Tag, TimeLog
from .forms import ImportUploadForm
from .services import parse_upload, validate_and_import


@dashboard_login_required
def import_export_home(request):
    form = ImportUploadForm(request.POST or None, request.FILES or None)
    results = None
    if request.method == "POST" and form.is_valid():
        rows = parse_upload(form.cleaned_data["file"])
        results = validate_and_import(rows, commit=form.cleaned_data["commit"])
    return render(request, "imports/home.html", {"form": form, "results": results})


@dashboard_login_required
def backup_export(request):
    data = {
        "clients": list(Client.objects.values()),
        "projects": list(Project.objects.values()),
        "milestones": list(Milestone.objects.values()),
        "payments": list(Payment.objects.values()),
        "time_logs": list(TimeLog.objects.values()),
        "notes": list(ProjectNote.objects.values()),
        "tags": list(Tag.objects.values()),
        "activities": list(Activity.objects.values()),
        "attachments": list(ProjectAttachment.objects.values("id", "project_id", "title", "file", "uploaded_at")),
    }
    response = HttpResponse(json.dumps(data, cls=DjangoJSONEncoder, indent=2), content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="freelance-dashboard-backup.json"'
    return response
