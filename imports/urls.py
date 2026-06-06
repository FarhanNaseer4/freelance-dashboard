from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("", views.import_export_home, name="home"),
    path("backup.json", views.backup_export, name="backup"),
]
