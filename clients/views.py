from django.db.models import Count, Q, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from core.auth import DashboardLoginRequiredMixin
from payments.models import Payment
from projects.models import Project
from .forms import ClientForm
from .models import Client


class ClientListView(DashboardLoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    paginate_by = 25

    def get_queryset(self):
        queryset = Client.objects.annotate(project_count=Count("projects")).order_by("name")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(company__icontains=query))
        return queryset


class ClientCreateView(DashboardLoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:list")


class ClientDetailView(DashboardLoginRequiredMixin, DetailView):
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        context["projects"] = client.projects.select_related("client").prefetch_related("payments", "milestones")
        context["revenue"] = (
            Payment.objects.filter(project__client=client, status=Payment.Status.RECEIVED)
            .values("date_received__year", "date_received__month")
            .annotate(total=Sum("amount"))
            .order_by("date_received__year", "date_received__month")
        )
        return context


class ClientHealthView(DashboardLoginRequiredMixin, TemplateView):
    template_name = "clients/client_health.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = Client.objects.annotate(project_count=Count("projects")).order_by("name")
        context["active_clients"] = clients.filter(projects__status__in=Project.ACTIVE_STATUSES).distinct()
        context["needs_followup"] = clients.filter(projects__follow_up_date__lte=timezone.localdate()).exclude(projects__status=Project.Status.COMPLETED).distinct()
        context["inactive_clients"] = clients.exclude(projects__status__in=Project.ACTIVE_STATUSES).distinct()
        context["high_value_clients"] = sorted(clients, key=lambda client: client.total_revenue, reverse=True)[:10]
        return context
