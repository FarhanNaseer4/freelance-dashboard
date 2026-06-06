from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("platform", models.CharField(choices=[("Fiverr", "Fiverr"), ("Upwork", "Upwork"), ("Direct", "Direct")], max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("company", models.CharField(blank=True, max_length=160)),
                ("notes", models.TextField(blank=True)),
                ("first_contact_date", models.DateField(blank=True, null=True)),
                ("last_contact_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
    ]
