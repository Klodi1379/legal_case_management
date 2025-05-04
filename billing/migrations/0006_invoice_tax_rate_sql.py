# Generated manually to add tax_rate to Invoice using SQL

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_timeentry_start_time_end_time'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE billing_invoice ADD COLUMN tax_rate decimal(5,2) NOT NULL DEFAULT 0.00;",
            reverse_sql="ALTER TABLE billing_invoice DROP COLUMN tax_rate;"
        ),
    ]
