# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_services', '0004_alter_llmmodel_created_at_alter_llmmodel_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='llmmodel',
            name='model_type',
            field=models.CharField(
                choices=[
                    ("gemma_3", "Gemma 3"),
                    ("gemma_2", "Gemma 2"),
                    ("llama_3", "Llama 3"),
                    ("mistral", "Mistral"),
                    ("other", "Other Open Source Model"),
                ],
                default="gemma_3",
                max_length=20,
                verbose_name="Model Type",
            ),
        ),
        migrations.AddField(
            model_name='llmmodel',
            name='model_version',
            field=models.CharField(
                default="3-12b-it-qat", max_length=50, verbose_name="Model Version"
            ),
        ),
        migrations.AddField(
            model_name='llmmodel',
            name='deployment_type',
            field=models.CharField(
                choices=[
                    ("local", "Local Deployment"),
                    ("containerized", "Containerized"),
                    ("api", "API Service"),
                    ("vllm", "vLLM Deployment"),
                ],
                default="api",
                max_length=20,
                verbose_name="Deployment Type",
            ),
        ),
        migrations.AddField(
            model_name='llmmodel',
            name='quantization',
            field=models.CharField(
                blank=True,
                help_text="Model quantization (e.g., 4bit, 8bit)",
                max_length=20,
                verbose_name="Quantization",
            ),
        ),
    ]
