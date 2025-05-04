# Generated manually to add start_time and end_time to TimeEntry

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_add_missing_fields_to_timeentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeentry',
            name='start_time',
            field=models.TimeField(blank=True, null=True, verbose_name='Start Time'),
        ),
        migrations.AddField(
            model_name='timeentry',
            name='end_time',
            field=models.TimeField(blank=True, null=True, verbose_name='End Time'),
        ),
    ]
