from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone


class ProjectQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=Project.ACTIVE_STATUSES)

    def due_this_week(self):
        today = timezone.localdate()
        return self.exclude(status=Project.Status.COMPLETED).filter(delivery_date__range=(today, today + timedelta(days=7)))

    def due_soon(self):
        today = timezone.localdate()
        return self.exclude(status=Project.Status.COMPLETED).filter(delivery_date__range=(today, today + timedelta(days=3)))

    def overdue(self):
        return self.exclude(status=Project.Status.COMPLETED).filter(delivery_date__lt=timezone.localdate())

    def with_pending_payment(self):
        return self.filter(Q(payments__status="Pending") | Q(budget__gt=0)).distinct()


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    color = models.CharField(max_length=20, default="#6366f1")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    class Platform(models.TextChoices):
        FIVERR = "Fiverr", "Fiverr"
        UPWORK = "Upwork", "Upwork"
        DIRECT = "Direct", "Direct"

    class ContractType(models.TextChoices):
        FIXED = "Fixed Price", "Fixed Price"
        MILESTONE = "Milestone Based", "Milestone Based"
        HOURLY = "Hourly", "Hourly"

    class ProjectType(models.TextChoices):
        WEB_SCRAPING = "Web Scraping", "Web Scraping"
        DATA_EXTRACTION = "Data Extraction", "Data Extraction"
        LEAD_GENERATION = "Lead Generation", "Lead Generation"
        DASHBOARD = "Dashboard Development", "Dashboard Development"
        DJANGO = "Django Development", "Django Development"
        AUTOMATION = "Automation", "Automation"
        POWER_BI = "Power BI", "Power BI"
        DATA_VIS = "Data Visualization", "Data Visualization"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        RUNNING = "Running", "Running"
        WORKING = "Working", "Working"
        WAITING_CLIENT = "Waiting Client", "Waiting Client"
        WAITING_CREDENTIALS = "Waiting Credentials", "Waiting Credentials"
        DATA_SHARED = "Data Shared", "Data Shared"
        DELIVERED = "Delivered", "Delivered"
        COMPLETED = "Completed", "Completed"
        ON_HOLD = "On Hold", "On Hold"

    class Priority(models.TextChoices):
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    ACTIVE_STATUSES = [Status.RUNNING, Status.WORKING, Status.WAITING_CLIENT, Status.WAITING_CREDENTIALS]

    client = models.ForeignKey("clients.Client", related_name="projects", on_delete=models.CASCADE)
    name = models.CharField(max_length=220)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    contract_type = models.CharField(max_length=30, choices=ContractType.choices)
    project_type = models.CharField(max_length=40, choices=ProjectType.choices)
    start_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    billed_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.RUNNING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    next_action = models.CharField(max_length=240, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="projects", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["delivery_date", "-priority", "name"]

    def __str__(self):
        return self.name

    @property
    def received_amount(self):
        from payments.models import Payment

        return self.payments.filter(status=Payment.Status.RECEIVED).aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

    @property
    def contract_received_amount(self):
        from payments.models import Payment

        return (
            self.payments.filter(status=Payment.Status.RECEIVED, category=Payment.Category.CONTRACT).aggregate(models.Sum("amount"))["amount__sum"]
            or Decimal("0")
        )

    @property
    def tip_amount(self):
        from payments.models import Payment

        return self.payments.filter(status=Payment.Status.RECEIVED, category=Payment.Category.TIP).aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

    @property
    def bonus_amount(self):
        from payments.models import Payment

        return self.payments.filter(status=Payment.Status.RECEIVED, category=Payment.Category.BONUS).aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

    @property
    def extra_earnings_amount(self):
        return self.tip_amount + self.bonus_amount

    @property
    def pending_amount(self):
        from payments.models import Payment

        return (
            self.payments.filter(status=Payment.Status.PENDING, category=Payment.Category.CONTRACT).aggregate(models.Sum("amount"))["amount__sum"]
            or Decimal("0")
        )

    @property
    def remaining_amount(self):
        if self.contract_type == self.ContractType.HOURLY and self.hourly_earnings > 0:
            return max(self.hourly_earnings - self.contract_received_amount, Decimal("0"))
        return max(self.budget - self.contract_received_amount, Decimal("0"))

    @property
    def hours_logged(self):
        return self.time_logs.aggregate(models.Sum("hours"))["hours__sum"] or Decimal("0")

    @property
    def hourly_earnings(self):
        return (self.hourly_rate or Decimal("0")) * self.hours_logged

    @property
    def hourly_cleared_hours(self):
        if self.contract_type != self.ContractType.HOURLY or not self.hourly_rate:
            return Decimal("0")
        return self.contract_received_amount / self.hourly_rate

    @property
    def hourly_uncleared_hours(self):
        return max(self.hours_logged - self.hourly_cleared_hours, Decimal("0"))

    @property
    def total_milestones_count(self):
        return self.milestones.count()

    @property
    def completed_milestones_count(self):
        return self.milestones.filter(status=Milestone.Status.COMPLETED).count()

    @property
    def current_milestone(self):
        return (
            self.milestones.filter(status=Milestone.Status.IN_PROGRESS).order_by("due_date", "id").first()
            or self.milestones.filter(status=Milestone.Status.PENDING).order_by("due_date", "id").first()
        )

    @property
    def milestone_received_amount(self):
        return self.milestones.filter(payment_status=Milestone.PaymentStatus.RECEIVED).aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

    @property
    def progress_percent(self):
        if self.contract_type == self.ContractType.MILESTONE:
            total = self.milestones.count()
            if not total:
                return 0
            completed = self.milestones.filter(status=Milestone.Status.COMPLETED).count()
            return round((completed / total) * 100)
        if self.status == self.Status.COMPLETED:
            return 100
        if self.status == self.Status.DELIVERED:
            return 85
        if self.status in [self.Status.RUNNING, self.Status.WORKING]:
            return 45
        if self.status == self.Status.ON_HOLD:
            return 20
        return 35

    @property
    def days_remaining(self):
        if not self.delivery_date:
            return None
        return (self.delivery_date - timezone.localdate()).days

    @property
    def is_overdue(self):
        return self.delivery_date and self.delivery_date < timezone.localdate() and self.status != self.Status.COMPLETED

    @property
    def is_due_soon(self):
        days = self.days_remaining
        return days is not None and 0 <= days <= 3 and self.status != self.Status.COMPLETED

    @property
    def has_pending_payment(self):
        return self.pending_amount > 0 or self.remaining_amount > 0


class Milestone(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        IN_PROGRESS = "In Progress", "In Progress"
        COMPLETED = "Completed", "Completed"

    class PaymentStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        RECEIVED = "Received", "Received"

    project = models.ForeignKey(Project, related_name="milestones", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    completion_date = models.DateField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    class Meta:
        ordering = ["due_date", "title"]

    def __str__(self):
        return f"{self.project} - {self.title}"


class TimeLog(models.Model):
    project = models.ForeignKey(Project, related_name="time_logs", on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    @property
    def earnings(self):
        return (self.project.hourly_rate or Decimal("0")) * self.hours


class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to="project_attachments/%Y/%m/")
    title = models.CharField(max_length=160, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ProjectNote(models.Model):
    project = models.ForeignKey(Project, related_name="project_notes", on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Activity(models.Model):
    project = models.ForeignKey(Project, related_name="activities", on_delete=models.CASCADE)
    action = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
