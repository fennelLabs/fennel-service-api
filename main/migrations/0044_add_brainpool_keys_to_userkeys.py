# Generated manually for brainpoolP256r1 ECDH keys (Whiteflag RFC 5639)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0043_add_p2p_ecdh_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="userkeys",
            name="private_brainpool_key",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name="userkeys",
            name="public_brainpool_key",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
