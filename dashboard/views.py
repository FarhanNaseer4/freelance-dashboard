import json
from calendar import monthrange
from datetime import date, timedelta

from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from core.auth import dashboard_login_required
from core.analytics import dashboard_alerts, dashboard_metrics, net_revenue_by_month, project_breakdowns, revenue_by_client, revenue_by_month, revenue_by_platform, revenue_by_project_type
from payments.models import Payment
from projects.models import Activity, Milestone, Project


@dashboard_login_required
def home(request):
    today = timezone.localdate()
    breakdowns = project_breakdowns()
    received = Payment.objects.filter(status=Payment.Status.RECEIVED)
    tip_bonus = received.filter(category__in=[Payment.Category.TIP, Payment.Category.BONUS]).aggregate(total=Sum("amount"))["total"] or 0
    context = {
        "metrics": dashboard_metrics(),
        "alerts": dashboard_alerts(),
        "today_followups": Project.objects.select_related("client").filter(follow_up_date=today).exclude(status=Project.Status.COMPLETED)[:6],
        "waiting_client": Project.objects.select_related("client").filter(status=Project.Status.WAITING_CLIENT)[:6],
        "recent_completed": Project.objects.select_related("client").filter(status=Project.Status.COMPLETED).order_by("-updated_at")[:6],
        "recent_activity": Activity.objects.select_related("project", "project__client")[:8],
        "tip_bonus": tip_bonus,
        "revenue_month_json": json.dumps(revenue_by_month()),
        "net_revenue_month_json": json.dumps(net_revenue_by_month()),
        "platform_revenue_json": json.dumps(revenue_by_platform()),
        "contract_type_json": json.dumps([{"label": row["contract_type"], "value": row["total"]} for row in breakdowns["contract_types"]]),
        "status_json": json.dumps([{"label": row["status"], "value": row["total"]} for row in breakdowns["statuses"]]),
        "recent_projects": Project.objects.select_related("client").exclude(status=Project.Status.COMPLETED)[:10],
    }
    return render(request, "dashboard/home.html", context)


@dashboard_login_required
def analytics(request):
    client_revenue = revenue_by_client()
    platform_revenue = revenue_by_platform()
    received = Payment.objects.filter(status=Payment.Status.RECEIVED)
    received_with_projects = received.select_related("project")
    contract_revenue = received.filter(category=Payment.Category.CONTRACT).aggregate(total=Sum("amount"))["total"] or 0
    tip_revenue = received.filter(category=Payment.Category.TIP).aggregate(total=Sum("amount"))["total"] or 0
    bonus_revenue = received.filter(category=Payment.Category.BONUS).aggregate(total=Sum("amount"))["total"] or 0
    pending_contract = Payment.objects.filter(status=Payment.Status.PENDING, category=Payment.Category.CONTRACT).aggregate(total=Sum("amount"))["total"] or 0
    uncleared_hourly = sum(project.remaining_amount for project in Project.objects.filter(contract_type=Project.ContractType.HOURLY))
    net_total_revenue = sum((payment.net_amount for payment in received_with_projects), 0)
    total_platform_fees = sum((payment.platform_fee_amount for payment in received_with_projects), 0)
    context = {
        "revenue_month_json": json.dumps(revenue_by_month()),
        "net_revenue_month_json": json.dumps(net_revenue_by_month()),
        "platform_revenue_json": json.dumps(platform_revenue),
        "project_type_json": json.dumps(revenue_by_project_type()),
        "client_revenue_json": json.dumps(client_revenue),
        "average_project_value": Project.objects.aggregate(avg=Avg("budget"))["avg"] or 0,
        "best_client": client_revenue[0] if client_revenue else None,
        "most_profitable_platform": platform_revenue[0] if platform_revenue else None,
        "total_revenue": received.aggregate(total=Sum("amount"))["total"] or 0,
        "net_total_revenue": net_total_revenue,
        "total_platform_fees": total_platform_fees,
        "contract_revenue": contract_revenue,
        "tip_revenue": tip_revenue,
        "bonus_revenue": bonus_revenue,
        "pending_contract": pending_contract,
        "uncleared_hourly": uncleared_hourly,
        "revenue_category_json": json.dumps(
            [
                {"label": "Contract", "value": float(contract_revenue)},
                {"label": "Tips", "value": float(tip_revenue)},
                {"label": "Bonus", "value": float(bonus_revenue)},
            ]
        ),
    }
    return render(request, "dashboard/analytics.html", context)


@dashboard_login_required
def calendar_view(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    first = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    events = []
    for project in Project.objects.select_related("client"):
        if project.delivery_date:
            events.append({"date": project.delivery_date, "type": "Delivery", "title": project.name, "project": project})
        if project.follow_up_date:
            events.append({"date": project.follow_up_date, "type": "Follow-up", "title": project.next_action or project.name, "project": project})
    for milestone in Milestone.objects.select_related("project", "project__client"):
        if milestone.due_date:
            events.append({"date": milestone.due_date, "type": "Milestone", "title": milestone.title, "project": milestone.project})
    events.sort(key=lambda item: item["date"])
    month_events = [event for event in events if event["date"].year == year and event["date"].month == month]
    weeks = []
    week = [None] * first.weekday()
    for day in range(1, days_in_month + 1):
        current = date(year, month, day)
        week.append({"date": current, "events": [event for event in month_events if event["date"] == current]})
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        week.extend([None] * (7 - len(week)))
        weeks.append(week)
    previous_month = first - timedelta(days=1)
    next_month = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    return render(
        request,
        "dashboard/calendar.html",
        {"events": events, "weeks": weeks, "month": first, "previous_month": previous_month, "next_month": next_month},
    )


@dashboard_login_required
def followup_inbox(request):
    today = timezone.localdate()
    context = {
        "due_today": Project.objects.select_related("client").filter(follow_up_date=today).exclude(status=Project.Status.COMPLETED),
        "overdue_followups": Project.objects.select_related("client").filter(follow_up_date__lt=today).exclude(status=Project.Status.COMPLETED),
        "waiting_client": Project.objects.select_related("client").filter(status=Project.Status.WAITING_CLIENT),
        "waiting_credentials": Project.objects.select_related("client").filter(status=Project.Status.WAITING_CREDENTIALS),
        "due_soon": Project.objects.select_related("client").due_soon(),
    }
    return render(request, "dashboard/followups.html", context)
