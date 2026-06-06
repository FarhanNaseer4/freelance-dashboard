from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.ClientListView.as_view(), name="list"),
    path("new/", views.ClientCreateView.as_view(), name="create"),
    path("health/", views.ClientHealthView.as_view(), name="health"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="detail"),
]
