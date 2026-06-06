from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="category",
            field=models.CharField(
                choices=[
                    ("Contract Payment", "Contract Payment"),
                    ("Tip", "Tip"),
                    ("Bonus", "Bonus"),
                ],
                default="Contract Payment",
                max_length=30,
            ),
        ),
    ]
