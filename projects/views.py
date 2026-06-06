import csv

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from openpyxl import Workbook

from core.auth import DashboardLoginRequiredMixin, dashboard_login_required
from payments.models import Payment
from .forms import MilestoneForm, PaymentForm, ProjectForm, TimeLogForm
from .models import Activity, Milestone, Project
from .services import settle_completed_project


def filtered_projects(request, mode="active"):
    queryset = Project.objects.select_related("client").prefetch_related("payments", "milestones", "tags")
    query = request.GET.get("q", "").strip()
    platform = request.GET.get("platform", "")
    status = request.GET.get("status", "")
    contract_type = request.GET.get("contract_type", "")
    priority = request.GET.get("priority", "")
    sort = request.GET.get("sort", "delivery_date")

    if mode == "active":
        queryset = queryset.exclude(status=Project.Status.COMPLETED)
    elif mode == "completed":
        queryset = queryset.filter(status=Project.Status.COMPLETED)

    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(client__name__icontains=query) | Q(next_action__icontains=query))
    if platform:
        queryset = queryset.filter(platform=platform)
    if status:
        queryset = queryset.filter(status=status)
    if contract_type:
        queryset = queryset.filter(contract_type=contract_type)
    if priority:
        queryset = queryset.filter(priority=priority)

    allowed_sorts = {
        "delivery_date",
        "-delivery_date",
        "budget",
        "-budget",
        "status",
        "priority",
        "name",
        "client__name",
    }
    if sort in allowed_sorts:
        queryset = queryset.order_by(sort)
    return queryset


class ProjectListView(DashboardLoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 25

    def get_queryset(self):
        return filtered_projects(self.request, mode="active")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["platforms"] = Project.Platform.choices
        context["statuses"] = Project.Status.choices
        context["contract_types"] = Project.ContractType.choices
        context["priorities"] = Project.Priority.choices
        context["filters"] = self.request.GET
        context["page_mode"] = "active"
        context["page_title"] = "Active Projects"
        context["empty_message"] = "No active projects found."
        return context


class CompletedProjectListView(DashboardLoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 25

    def get_queryset(self):
        return filtered_projects(self.request, mode="completed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["platforms"] = Project.Platform.choices
        context["statuses"] = Project.Status.choices
        context["contract_types"] = Project.ContractType.choices
        context["priorities"] = Project.Priority.choices
        context["filters"] = self.request.GET
        context["page_mode"] = "completed"
        context["page_title"] = "Completed Projects"
        context["empty_message"] = "No completed projects found."
        return context


class ProjectPipelineView(DashboardLoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/pipeline.html"
    context_object_name = "projects"

    pipeline_statuses = [
        Project.Status.RUNNING,
        Project.Status.WORKING,
        Project.Status.WAITING_CLIENT,
        Project.Status.WAITING_CREDENTIALS,
        Project.Status.DELIVERED,
    ]

    def get_queryset(self):
        return Project.objects.select_related("client").prefetch_related("payments", "tags").filter(status__in=self.pipeline_statuses)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = list(context["projects"])
        context["columns"] = [{"status": status, "projects": [project for project in projects if project.status == status]} for status in self.pipeline_statuses]
        return context


class ProjectCreateView(DashboardLoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.status == Project.Status.COMPLETED:
            settle_completed_project(self.object, received_date=self.object.delivery_date or timezone.localdate())
        Activity.objects.create(project=self.object, action="Project created", description="Created from dashboard form.")
        return response


class ProjectDetailView(DashboardLoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"
    queryset = Project.objects.select_related("client").prefetch_related(
        "milestones", "time_logs", "payments", "attachments", "project_notes", "activities", "tags"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["time_log_form"] = TimeLogForm()
        context["payment_form"] = PaymentForm(
            initial={"payment_method": self.object.platform, "status": Payment.Status.RECEIVED, "category": Payment.Category.CONTRACT}
        )
        context["milestone_form"] = MilestoneForm()
        return context


class ProjectUpdateView(DashboardLoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.status == Project.Status.COMPLETED:
            settle_completed_project(self.object, received_date=self.object.delivery_date or timezone.localdate())
            Activity.objects.create(project=self.object, action="Payment settled", description="Contract payment synced after completion.")
        return response


@dashboard_login_required
def add_time_log(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = TimeLogForm(request.POST)
    if request.method == "POST" and form.is_valid():
        time_log = form.save(commit=False)
        time_log.project = project
        time_log.save()
        Activity.objects.create(project=project, action="Hours logged", description=f"Logged {time_log.hours} hours.")
    return redirect("projects:detail", pk=project.pk)


@dashboard_login_required
def add_payment(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = PaymentForm(request.POST)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.project = project
        payment.save()
        Activity.objects.create(project=project, action="Payment recorded", description=f"{payment.status}: ${payment.amount}.")
    return redirect("projects:detail", pk=project.pk)


@dashboard_login_required
def add_milestone(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = MilestoneForm(request.POST)
    if request.method == "POST" and form.is_valid():
        milestone = form.save(commit=False)
        milestone.project = project
        milestone.save()
        Activity.objects.create(project=project, action="Milestone added", description=milestone.title)
    return redirect("projects:detail", pk=project.pk)


@dashboard_login_required
def edit_payment(request, pk, payment_id):
    project = get_object_or_404(Project, pk=pk)
    payment = get_object_or_404(Payment, pk=payment_id, project=project)
    form = PaymentForm(request.POST or None, instance=payment)
    if request.method == "POST" and form.is_valid():
        form.save()
        Activity.objects.create(project=project, action="Payment edited", description=f"Updated ${payment.amount}.")
        return redirect("projects:detail", pk=project.pk)
    return render_edit_form(request, project, form, "Edit Payment")


@dashboard_login_required
def edit_milestone(request, pk, milestone_id):
    project = get_object_or_404(Project, pk=pk)
    milestone = get_object_or_404(Milestone, pk=milestone_id, project=project)
    form = MilestoneForm(request.POST or None, instance=milestone)
    if request.method == "POST" and form.is_valid():
        form.save()
        Activity.objects.create(project=project, action="Milestone edited", description=milestone.title)
        return redirect("projects:detail", pk=project.pk)
    return render_edit_form(request, project, form, "Edit Milestone")


def render_edit_form(request, project, form, title):
    from django.shortcuts import render

    return render(request, "projects/inline_form.html", {"project": project, "form": form, "title": title})


@dashboard_login_required
def mark_milestone_complete(request, pk, milestone_id):
    project = get_object_or_404(Project, pk=pk)
    milestone = get_object_or_404(Milestone, pk=milestone_id, project=project)
    if request.method == "POST":
        milestone.status = Milestone.Status.COMPLETED
        milestone.completion_date = milestone.completion_date or timezone.localdate()
        milestone.save(update_fields=["status", "completion_date"])
        Activity.objects.create(project=project, action="Milestone completed", description=milestone.title)
    return redirect("projects:detail", pk=project.pk)


@dashboard_login_required
def mark_milestone_paid(request, pk, milestone_id):
    project = get_object_or_404(Project, pk=pk)
    milestone = get_object_or_404(Milestone, pk=milestone_id, project=project)
    if request.method == "POST":
        milestone.payment_status = Milestone.PaymentStatus.RECEIVED
        milestone.save(update_fields=["payment_status"])
        Payment.objects.create(
            project=project,
            amount=milestone.amount,
            category=Payment.Category.CONTRACT,
            payment_method=Payment.Method.UPWORK if project.platform == Project.Platform.UPWORK else Payment.Method.FIVERR if project.platform == Project.Platform.FIVERR else Payment.Method.WISE,
            status=Payment.Status.RECEIVED,
            date_received=timezone.localdate(),
        )
        Activity.objects.create(project=project, action="Milestone paid", description=milestone.title)
    return redirect("projects:detail", pk=project.pk)


@dashboard_login_required
def quick_update_status(request, pk, status):
    project = get_object_or_404(Project, pk=pk)
    valid_statuses = {choice[0] for choice in Project.Status.choices}
    if request.method == "POST" and status in valid_statuses:
        old_status = project.status
        project.status = status
        project.save(update_fields=["status"])
        if project.status == Project.Status.COMPLETED:
            settle_completed_project(project, received_date=project.delivery_date or timezone.localdate())
        Activity.objects.create(project=project, action="Status changed", description=f"{old_status} -> {status}")
    return redirect(request.POST.get("next") or "projects:list")


@dashboard_login_required
def export_projects_csv(request):
    mode = request.GET.get("mode", "active")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="projects.csv"'
    writer = csv.writer(response)
    writer.writerow(["Client", "Platform", "Project", "Contract Type", "Budget", "Contract Received", "Tips/Bonus", "Remaining", "Delivery Date", "Status", "Priority", "Next Action"])
    for project in filtered_projects(request, mode=mode):
        writer.writerow([
            project.client.name,
            project.platform,
            project.name,
            project.contract_type,
            project.budget,
            project.contract_received_amount,
            project.extra_earnings_amount,
            project.remaining_amount,
            project.delivery_date,
            project.status,
            project.priority,
            project.next_action,
        ])
    return response


@dashboard_login_required
def export_projects_excel(request):
    mode = request.GET.get("mode", "active")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet.append(["Client", "Platform", "Project", "Contract Type", "Budget", "Contract Received", "Tips/Bonus", "Remaining", "Delivery Date", "Status", "Priority", "Next Action"])
    for project in filtered_projects(request, mode=mode):
        sheet.append([
            project.client.name,
            project.platform,
            project.name,
            project.contract_type,
            float(project.budget),
            float(project.contract_received_amount),
            float(project.extra_earnings_amount),
            float(project.remaining_amount),
            project.delivery_date.isoformat() if project.delivery_date else "",
            project.status,
            project.priority,
            project.next_action,
        ])
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="projects.xlsx"'
    workbook.save(response)
    return response
