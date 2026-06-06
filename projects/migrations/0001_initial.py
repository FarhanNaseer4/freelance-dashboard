from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("color", models.CharField(default="#6366f1", max_length=20)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=220)),
                ("platform", models.CharField(choices=[("Fiverr", "Fiverr"), ("Upwork", "Upwork"), ("Direct", "Direct")], max_length=20)),
                ("contract_type", models.CharField(choices=[("Fixed Price", "Fixed Price"), ("Milestone Based", "Milestone Based"), ("Hourly", "Hourly")], max_length=30)),
                ("project_type", models.CharField(choices=[("Web Scraping", "Web Scraping"), ("Data Extraction", "Data Extraction"), ("Lead Generation", "Lead Generation"), ("Dashboard Development", "Dashboard Development"), ("Django Development", "Django Development"), ("Automation", "Automation"), ("Power BI", "Power BI"), ("Data Visualization", "Data Visualization"), ("Other", "Other")], max_length=40)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                ("budget", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("hourly_rate", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("expected_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("billed_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("status", models.CharField(choices=[("Running", "Running"), ("Working", "Working"), ("Waiting Client", "Waiting Client"), ("Waiting Credentials", "Waiting Credentials"), ("Delivered", "Delivered"), ("Completed", "Completed"), ("On Hold", "On Hold")], default="Running", max_length=30)),
                ("priority", models.CharField(choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")], default="Medium", max_length=10)),
                ("description", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("next_action", models.CharField(blank=True, max_length=240)),
                ("follow_up_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="clients.client")),
                ("tags", models.ManyToManyField(blank=True, related_name="projects", to="projects.tag")),
            ],
            options={"ordering": ["delivery_date", "-priority", "name"]},
        ),
        migrations.CreateModel(
            name="Milestone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("Pending", "Pending"), ("In Progress", "In Progress"), ("Completed", "Completed")], default="Pending", max_length=20)),
                ("completion_date", models.DateField(blank=True, null=True)),
                ("delivery_notes", models.TextField(blank=True)),
                ("payment_status", models.CharField(choices=[("Pending", "Pending"), ("Received", "Received")], default="Pending", max_length=20)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="milestones", to="projects.project")),
            ],
            options={"ordering": ["due_date", "title"]},
        ),
        migrations.CreateModel(
            name="TimeLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("hours", models.DecimalField(decimal_places=2, max_digits=8)),
                ("description", models.TextField(blank=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="time_logs", to="projects.project")),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.CreateModel(
            name="ProjectAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="project_attachments/%Y/%m/")),
                ("title", models.CharField(blank=True, max_length=160)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="projects.project")),
            ],
        ),
        migrations.CreateModel(
            name="ProjectNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_notes", to="projects.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Activity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="projects.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
