from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("analytics/", views.analytics, name="analytics"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("follow-ups/", views.followup_inbox, name="followups"),
]
