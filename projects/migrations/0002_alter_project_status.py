from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("Running", "Running"),
                    ("Working", "Working"),
                    ("Waiting Client", "Waiting Client"),
                    ("Waiting Credentials", "Waiting Credentials"),
                    ("Data Shared", "Data Shared"),
                    ("Delivered", "Delivered"),
                    ("Completed", "Completed"),
                    ("On Hold", "On Hold"),
                ],
                default="Running",
                max_length=30,
            ),
        ),
    ]
