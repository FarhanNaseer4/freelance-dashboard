from django.db import models
from decimal import Decimal


class Payment(models.Model):
    class Category(models.TextChoices):
        CONTRACT = "Contract Payment", "Contract Payment"
        TIP = "Tip", "Tip"
        BONUS = "Bonus", "Bonus"

    class Method(models.TextChoices):
        FIVERR = "Fiverr", "Fiverr"
        UPWORK = "Upwork", "Upwork"
        PAYPAL = "PayPal", "PayPal"
        WISE = "Wise", "Wise"
        BANK = "Bank Transfer", "Bank Transfer"

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        RECEIVED = "Received", "Received"

    project = models.ForeignKey("projects.Project", related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.CONTRACT)
    date_received = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=30, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_received", "-created_at"]

    def __str__(self):
        return f"{self.project} - {self.amount} ({self.category}, {self.status})"

    @property
    def platform_fee_rate(self):
        if self.project.platform == "Fiverr":
            return Decimal("0.20")
        if self.project.platform == "Upwork":
            return Decimal("0.10")
        return Decimal("0")

    @property
    def platform_fee_amount(self):
        if self.status != self.Status.RECEIVED:
            return Decimal("0")
        return self.amount * self.platform_fee_rate

    @property
    def net_amount(self):
        if self.status != self.Status.RECEIVED:
            return Decimal("0")
        return self.amount - self.platform_fee_amount
