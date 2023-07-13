# Generated by Django 4.1.10 on 2023-07-13 12:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("main", "0014_userkeys_private_diffie_hellman_key_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userkeys",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="keys",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
