# Generated manually on 2025-10-10
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_signal_message_code_signal_subject_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='signal',
            name='block_number',
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='signal',
            name='block_hash',
            field=models.CharField(blank=True, max_length=66, null=True),
        ),
        migrations.AddField(
            model_name='signal',
            name='extrinsic_index',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='signal',
            name='finalized',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='signal',
            name='execution_success',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
