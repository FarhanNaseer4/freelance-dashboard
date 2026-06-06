from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("date_received", models.DateField(blank=True, null=True)),
                ("payment_method", models.CharField(choices=[("Fiverr", "Fiverr"), ("Upwork", "Upwork"), ("PayPal", "PayPal"), ("Wise", "Wise"), ("Bank Transfer", "Bank Transfer")], max_length=30)),
                ("status", models.CharField(choices=[("Pending", "Pending"), ("Received", "Received")], default="Pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="projects.project")),
            ],
            options={"ordering": ["-date_received", "-created_at"]},
        ),
    ]
