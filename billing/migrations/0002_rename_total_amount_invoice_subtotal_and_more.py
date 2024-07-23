# Generated by Django 5.0.7 on 2024-07-23 13:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="invoice",
            old_name="total_amount",
            new_name="subtotal",
        ),
        migrations.RenameField(
            model_name="invoiceitem",
            old_name="total_price",
            new_name="amount",
        ),
        migrations.RenameField(
            model_name="invoiceitem",
            old_name="unit_price",
            new_name="rate",
        ),
        migrations.RenameField(
            model_name="timeentry",
            old_name="billable",
            new_name="is_billable",
        ),
        migrations.RemoveField(
            model_name="timeentry",
            name="lawyer",
        ),
        migrations.AddField(
            model_name="invoice",
            name="tax",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="invoice",
            name="total",
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timeentry",
            name="rate",
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timeentry",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="invoiceitem",
            name="description",
            field=models.TextField(),
        ),
        migrations.CreateModel(
            name="Payment",
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
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("payment_date", models.DateField()),
                ("payment_method", models.CharField(max_length=50)),
                (
                    "transaction_id",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="billing.invoice",
                    ),
                ),
            ],
        ),
    ]
