# Generated by Django 4.1.10 on 2023-07-12 18:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0009_transaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="signal",
            name="confirmed_timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ConfirmationRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "confirmer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="confirmations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "signal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="confirmations",
                        to="main.signal",
                    ),
                ),
            ],
        ),
    ]