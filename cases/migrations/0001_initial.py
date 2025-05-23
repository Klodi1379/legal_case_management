# Generated by Django 5.0.7 on 2024-07-23 00:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Case",
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
                ("title", models.CharField(max_length=255)),
                ("case_number", models.CharField(max_length=50, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("OPEN", "Open"),
                            ("CLOSED", "Closed"),
                            ("PENDING", "Pending"),
                        ],
                        default="OPEN",
                        max_length=10,
                    ),
                ),
                (
                    "case_type",
                    models.CharField(
                        choices=[
                            ("CIVIL", "Civil"),
                            ("CRIMINAL", "Criminal"),
                            ("CORPORATE", "Corporate"),
                            ("FAMILY", "Family"),
                            ("OTHER", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField()),
                ("open_date", models.DateField(auto_now_add=True)),
                ("close_date", models.DateField(blank=True, null=True)),
                (
                    "assigned_lawyer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_cases",
                        to="accounts.user",
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cases",
                        to="clients.client",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CaseNote",
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
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="accounts.user"
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notes",
                        to="cases.case",
                    ),
                ),
            ],
        ),
    ]
