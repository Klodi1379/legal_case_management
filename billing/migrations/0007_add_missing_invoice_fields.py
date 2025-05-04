# Generated manually

from django.db import migrations, models
from decimal import Decimal
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0006_invoice_tax_rate_sql'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=models.CASCADE,
                related_name='created_invoices',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Created By'
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='discount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=10,
                verbose_name='Discount'
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                null=True,
                verbose_name='Created At'
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                null=True,
                verbose_name='Updated At'
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='notes',
            field=models.TextField(
                blank=True,
                verbose_name='Notes'
            ),
        ),
    ]
