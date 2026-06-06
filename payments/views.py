from django.db.models import Q
from django.views.generic import ListView

from core.auth import DashboardLoginRequiredMixin
from .models import Payment


class PaymentListView(DashboardLoginRequiredMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"
    context_object_name = "payments"
    paginate_by = 30

    def get_queryset(self):
        queryset = Payment.objects.select_related("project", "project__client")
        status = self.request.GET.get("status")
        query = self.request.GET.get("q", "").strip()
        if status:
            queryset = queryset.filter(status=status)
        if query:
            queryset = queryset.filter(Q(project__name__icontains=query) | Q(project__client__name__icontains=query))
        return queryset
