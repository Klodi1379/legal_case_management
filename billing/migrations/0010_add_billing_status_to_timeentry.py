# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0009_alter_invoice_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeentry',
            name='billing_status',
            field=models.CharField(choices=[('BILLABLE', 'Billable'), ('NON_BILLABLE', 'Non-Billable'), ('NO_CHARGE', 'No Charge')], default='BILLABLE', max_length=20, verbose_name='Billing Status'),
        ),
    ]
