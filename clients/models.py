from decimal import Decimal

from django.db import models


class Client(models.Model):
    class Platform(models.TextChoices):
        FIVERR = "Fiverr", "Fiverr"
        UPWORK = "Upwork", "Upwork"
        DIRECT = "Direct", "Direct"

    name = models.CharField(max_length=160)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    first_contact_date = models.DateField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total_revenue(self):
        from payments.models import Payment

        return (
            Payment.objects.filter(project__client=self, status=Payment.Status.RECEIVED).aggregate(models.Sum("amount"))["amount__sum"]
            or Decimal("0")
        )

    @property
    def completed_projects_count(self):
        return self.projects.filter(status="Completed").count()

    @property
    def active_projects_count(self):
        return self.projects.exclude(status__in=["Completed", "Delivered", "On Hold"]).count()
