# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_activitycode_expense_expensecategory_trustaccount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeentry',
            name='activity_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='time_entries', to='billing.activitycode', verbose_name='Activity Code'),
        ),
    ]
