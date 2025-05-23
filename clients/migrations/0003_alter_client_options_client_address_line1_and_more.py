# Generated by Django 5.0.4 on 2025-04-26 00:19

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_alter_client_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="client",
            options={
                "ordering": ["last_name", "first_name", "company_name"],
                "verbose_name": "Client",
                "verbose_name_plural": "Clients",
            },
        ),
        migrations.AddField(
            model_name="client",
            name="address_line1",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Address Line 1"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="address_line2",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Address Line 2"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="city",
            field=models.CharField(blank=True, max_length=100, verbose_name="City"),
        ),
        migrations.AddField(
            model_name="client",
            name="client_type",
            field=models.CharField(
                choices=[
                    ("INDIVIDUAL", "Individual"),
                    ("ORGANIZATION", "Organization"),
                ],
                default="INDIVIDUAL",
                max_length=20,
                verbose_name="Client Type",
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="country",
            field=models.CharField(blank=True, max_length=100, verbose_name="Country"),
        ),
        migrations.AddField(
            model_name="client",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="Created At",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="client",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True, verbose_name="Date of Birth"),
        ),
        migrations.AddField(
            model_name="client",
            name="email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Email"),
        ),
        migrations.AddField(
            model_name="client",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="First Name"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="client",
            name="last_name",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="Last Name"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="mobile",
            field=models.CharField(blank=True, max_length=20, verbose_name="Mobile"),
        ),
        migrations.AddField(
            model_name="client",
            name="phone",
            field=models.CharField(blank=True, max_length=20, verbose_name="Phone"),
        ),
        migrations.AddField(
            model_name="client",
            name="postal_code",
            field=models.CharField(
                blank=True, max_length=20, verbose_name="Postal Code"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="ssn_last_four",
            field=models.CharField(
                blank=True, max_length=4, verbose_name="Last 4 of SSN"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="state",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="State/Province"
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="tax_id",
            field=models.CharField(blank=True, max_length=50, verbose_name="Tax ID"),
        ),
        migrations.AddField(
            model_name="client",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="client",
            name="company_name",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Company Name"
            ),
        ),
        migrations.AlterField(
            model_name="client",
            name="industry",
            field=models.CharField(blank=True, max_length=100, verbose_name="Industry"),
        ),
        migrations.AlterField(
            model_name="client",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Notes"),
        ),
        migrations.AlterField(
            model_name="client",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="ClientContact",
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
                (
                    "first_name",
                    models.CharField(max_length=100, verbose_name="First Name"),
                ),
                (
                    "last_name",
                    models.CharField(max_length=100, verbose_name="Last Name"),
                ),
                (
                    "position",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Position"
                    ),
                ),
                (
                    "email",
                    models.EmailField(blank=True, max_length=254, verbose_name="Email"),
                ),
                (
                    "phone",
                    models.CharField(blank=True, max_length=20, verbose_name="Phone"),
                ),
                (
                    "mobile",
                    models.CharField(blank=True, max_length=20, verbose_name="Mobile"),
                ),
                (
                    "is_primary_contact",
                    models.BooleanField(default=False, verbose_name="Primary Contact"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts",
                        to="clients.client",
                    ),
                ),
            ],
            options={
                "verbose_name": "Client Contact",
                "verbose_name_plural": "Client Contacts",
                "ordering": ["last_name", "first_name"],
            },
        ),
    ]
