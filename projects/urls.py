from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("new/", views.ProjectCreateView.as_view(), name="create"),
    path("pipeline/", views.ProjectPipelineView.as_view(), name="pipeline"),
    path("completed/", views.CompletedProjectListView.as_view(), name="completed"),
    path("export/csv/", views.export_projects_csv, name="export_csv"),
    path("export/excel/", views.export_projects_excel, name="export_excel"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path("<int:pk>/time-logs/add/", views.add_time_log, name="add_time_log"),
    path("<int:pk>/payments/add/", views.add_payment, name="add_payment"),
    path("<int:pk>/payments/<int:payment_id>/edit/", views.edit_payment, name="edit_payment"),
    path("<int:pk>/milestones/add/", views.add_milestone, name="add_milestone"),
    path("<int:pk>/milestones/<int:milestone_id>/edit/", views.edit_milestone, name="edit_milestone"),
    path("<int:pk>/milestones/<int:milestone_id>/complete/", views.mark_milestone_complete, name="mark_milestone_complete"),
    path("<int:pk>/milestones/<int:milestone_id>/paid/", views.mark_milestone_paid, name="mark_milestone_paid"),
    path("<int:pk>/status/<str:status>/", views.quick_update_status, name="quick_status"),
]
