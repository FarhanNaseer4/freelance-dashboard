from calendar import month_name
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from clients.models import Client
from payments.models import Payment
from projects.models import Project


def dashboard_metrics():
    today = timezone.localdate()
    month_start = today.replace(day=1)
    next_month_start = month_start.replace(year=month_start.year + 1, month=1) if month_start.month == 12 else month_start.replace(month=month_start.month + 1)
    year_start = today.replace(month=1, day=1)
    received = Payment.objects.filter(status=Payment.Status.RECEIVED)
    month_received = received.filter(date_received__gte=month_start, date_received__lt=next_month_start)
    year_received = received.filter(date_received__gte=year_start)
    return {
        "active_projects": Project.objects.active().count(),
        "due_this_week": Project.objects.due_this_week().count(),
        "pending_payments": Payment.objects.filter(status=Payment.Status.PENDING).count(),
        "total_revenue": received.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "total_net_revenue": sum((payment.net_amount for payment in received.select_related("project")), Decimal("0")),
        "revenue_this_month": month_received.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "net_revenue_this_month": sum((payment.net_amount for payment in month_received.select_related("project")), Decimal("0")),
        "platform_fees_this_month": sum((payment.platform_fee_amount for payment in month_received.select_related("project")), Decimal("0")),
        "revenue_this_year": year_received.aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "net_revenue_this_year": sum((payment.net_amount for payment in year_received.select_related("project")), Decimal("0")),
        "active_clients": Client.objects.filter(projects__status__in=Project.ACTIVE_STATUSES).distinct().count(),
        "completed_projects": Project.objects.filter(status=Project.Status.COMPLETED).count(),
    }


def revenue_by_month():
    rows = (
        Payment.objects.filter(status=Payment.Status.RECEIVED, date_received__isnull=False)
        .annotate(month=TruncMonth("date_received"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    return [{"label": f"{month_name[row['month'].month]} {row['month'].year}", "value": float(row["total"] or 0)} for row in rows]


def net_revenue_by_month():
    payments = Payment.objects.filter(status=Payment.Status.RECEIVED, date_received__isnull=False).select_related("project").order_by("date_received")
    totals = {}
    for payment in payments:
        key = payment.date_received.replace(day=1)
        totals[key] = totals.get(key, Decimal("0")) + payment.net_amount
    return [{"label": f"{month_name[month.month]} {month.year}", "value": float(total)} for month, total in sorted(totals.items())]


def revenue_by_platform():
    rows = (
        Payment.objects.filter(status=Payment.Status.RECEIVED)
        .values("project__platform")
        .annotate(total=Sum("amount"))
        .order_by("project__platform")
    )
    return [{"label": row["project__platform"], "value": float(row["total"] or 0)} for row in rows]


def revenue_by_project_type():
    rows = (
        Payment.objects.filter(status=Payment.Status.RECEIVED)
        .values("project__project_type")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    return [{"label": row["project__project_type"], "value": float(row["total"] or 0)} for row in rows]


def revenue_by_client():
    rows = (
        Payment.objects.filter(status=Payment.Status.RECEIVED)
        .values("project__client__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    return [{"label": row["project__client__name"], "value": float(row["total"] or 0)} for row in rows]


def project_breakdowns():
    return {
        "contract_types": list(Project.objects.values("contract_type").annotate(total=Count("id")).order_by("contract_type")),
        "statuses": list(Project.objects.values("status").annotate(total=Count("id")).order_by("status")),
    }


def dashboard_alerts():
    today = timezone.localdate()
    return {
        "due_soon": Project.objects.due_soon()[:8],
        "overdue": Project.objects.overdue()[:8],
        "followups": Project.objects.filter(follow_up_date__lte=today).exclude(status=Project.Status.COMPLETED)[:8],
        "pending_payments": Project.objects.with_pending_payment()[:8],
    }
