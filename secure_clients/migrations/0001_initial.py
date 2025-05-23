# Generated by Django 5.0.7 on 2025-05-03 19:35

import core.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0004_alter_client_address_line1_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecureClientData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='First Name')),
                ('last_name', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='Last Name')),
                ('ssn_last_four', core.fields.EncryptedCharField(blank=True, max_length=4, verbose_name='Last 4 of SSN')),
                ('email', core.fields.EncryptedCharField(blank=True, max_length=254, verbose_name='Email')),
                ('phone', core.fields.EncryptedCharField(blank=True, max_length=20, verbose_name='Phone')),
                ('mobile', core.fields.EncryptedCharField(blank=True, max_length=20, verbose_name='Mobile')),
                ('address_line1', core.fields.EncryptedCharField(blank=True, max_length=255, verbose_name='Address Line 1')),
                ('address_line2', core.fields.EncryptedCharField(blank=True, max_length=255, verbose_name='Address Line 2')),
                ('city', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='City')),
                ('state', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='State/Province')),
                ('postal_code', core.fields.EncryptedCharField(blank=True, max_length=20, verbose_name='Postal Code')),
                ('country', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='Country')),
                ('company_name', core.fields.EncryptedCharField(blank=True, max_length=255, verbose_name='Company Name')),
                ('tax_id', core.fields.EncryptedCharField(blank=True, max_length=50, verbose_name='Tax ID')),
                ('notes', core.fields.EncryptedTextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('client', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='secure_data', to='clients.client')),
            ],
            options={
                'verbose_name': 'Secure Client Data',
                'verbose_name_plural': 'Secure Client Data',
            },
        ),
        migrations.CreateModel(
            name='SecureContactData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='First Name')),
                ('last_name', core.fields.EncryptedCharField(blank=True, max_length=100, verbose_name='Last Name')),
                ('email', core.fields.EncryptedCharField(blank=True, max_length=254, verbose_name='Email')),
                ('phone', core.fields.EncryptedCharField(blank=True, max_length=20, verbose_name='Phone')),
                ('mobile', core.fields.EncryptedCharField(blank=True, max_length=20, verbose_name='Mobile')),
                ('notes', core.fields.EncryptedTextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('contact', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='secure_data', to='clients.clientcontact')),
            ],
            options={
                'verbose_name': 'Secure Contact Data',
                'verbose_name_plural': 'Secure Contact Data',
            },
        ),
    ]
