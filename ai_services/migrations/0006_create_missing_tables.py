# Generated manually

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ai_services', '0005_add_missing_fields_to_llmmodel'),
        ('cases', '0002_court_practicearea_alter_case_options_and_more'),
        ('documents', '0003_documenttag_documenttagged_documenttemplate_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PromptTemplate",
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
                    "name",
                    models.CharField(max_length=100, verbose_name="Template Name"),
                ),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("document_summarization", "Document Summarization"),
                            ("key_points", "Extract Key Points"),
                            ("legal_analysis", "Legal Analysis"),
                            ("precedent_search", "Find Relevant Precedents"),
                            ("legal_research", "Legal Research"),
                            ("document_generation", "Document Generation"),
                            ("contract_analysis", "Contract Analysis"),
                            ("client_intake", "Client Intake Processing"),
                            ("custom", "Custom Task"),
                        ],
                        max_length=30,
                        verbose_name="Task Type",
                    ),
                ),
                ("prompt_template", models.TextField(verbose_name="Prompt Template")),
                (
                    "system_prompt",
                    models.TextField(
                        blank=True,
                        help_text="System prompt for models that support it",
                        verbose_name="System Prompt",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is Active"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_prompts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "suitable_models",
                    models.ManyToManyField(
                        blank=True,
                        related_name="suitable_prompts",
                        to="ai_services.llmmodel",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prompt Template",
                "verbose_name_plural": "Prompt Templates",
            },
        ),
        migrations.CreateModel(
            name="AIAnalysisRequest",
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
                    "analysis_type",
                    models.CharField(
                        choices=[
                            ("DOCUMENT_SUMMARY", "Document Summary"),
                            ("KEY_POINTS", "Key Points"),
                            ("LEGAL_ANALYSIS", "Legal Analysis"),
                            ("PRECEDENT_SEARCH", "Precedent Search"),
                            ("CONTRACT_REVIEW", "Contract Review"),
                            ("LEGAL_RESEARCH", "Legal Research"),
                            ("DOCUMENT_GENERATION", "Document Generation"),
                            ("CUSTOM", "Custom Analysis"),
                        ],
                        max_length=50,
                        verbose_name="Analysis Type",
                    ),
                ),
                (
                    "input_text",
                    models.TextField(
                        blank=True,
                        help_text="Input text for analysis (if not using a document)",
                        verbose_name="Input Text",
                    ),
                ),
                (
                    "combined_prompt",
                    models.TextField(
                        help_text="The full prompt sent to the LLM",
                        verbose_name="Combined Prompt",
                    ),
                ),
                (
                    "custom_instructions",
                    models.TextField(blank=True, verbose_name="Custom Instructions"),
                ),
                (
                    "context_items",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="IDs of documents or other items used for context",
                        verbose_name="Context Items",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PROCESSING", "Processing"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Completed At"
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_analyses",
                        to="cases.case",
                        verbose_name="Case",
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_analyses",
                        to="documents.document",
                        verbose_name="Document",
                    ),
                ),
                (
                    "llm_model",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="analysis_requests",
                        to="ai_services.llmmodel",
                        verbose_name="LLM Model",
                    ),
                ),
                (
                    "prompt_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="analysis_requests",
                        to="ai_services.prompttemplate",
                        verbose_name="Prompt Template",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requested_analyses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Requested By",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI Analysis Request",
                "verbose_name_plural": "AI Analysis Requests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIAnalysisResult",
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
                ("output_text", models.TextField(verbose_name="Output Text")),
                (
                    "raw_response",
                    models.JSONField(default=dict, verbose_name="Raw Response"),
                ),
                (
                    "tokens_used",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Tokens Used"
                    ),
                ),
                (
                    "processing_time",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Processing Time (seconds)"
                    ),
                ),
                (
                    "has_error",
                    models.BooleanField(default=False, verbose_name="Has Error"),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="Error Message"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "analysis_request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="result",
                        to="ai_services.aianalysisrequest",
                        verbose_name="Analysis Request",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI Analysis Result",
                "verbose_name_plural": "AI Analysis Results",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AIGeneratedDocument",
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
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "is_approved",
                    models.BooleanField(default=False, verbose_name="Approved"),
                ),
                (
                    "analysis_result",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="generated_documents",
                        to="ai_services.aianalysisresult",
                        verbose_name="Analysis Result",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_ai_documents",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Approved By",
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_generated_documents",
                        to="cases.case",
                        verbose_name="Case",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_generated_documents",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "document",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_source",
                        to="documents.document",
                        verbose_name="Document",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI Generated Document",
                "verbose_name_plural": "AI Generated Documents",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DocumentEmbedding",
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
                    "vector_id",
                    models.CharField(
                        help_text="ID in the vector store",
                        max_length=100,
                        verbose_name="Vector ID",
                    ),
                ),
                (
                    "embedding_model",
                    models.CharField(max_length=100, verbose_name="Embedding Model"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "last_updated",
                    models.DateTimeField(auto_now=True, verbose_name="Last Updated"),
                ),
                (
                    "document",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embedding",
                        to="documents.document",
                        verbose_name="Document",
                    ),
                ),
                (
                    "vector_store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_embeddings",
                        to="ai_services.vectorstore",
                        verbose_name="Vector Store",
                    ),
                ),
            ],
            options={
                "verbose_name": "Document Embedding",
                "verbose_name_plural": "Document Embeddings",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="aianalysisrequest",
            index=models.Index(
                fields=["status", "-created_at"], name="ai_services_status_d79265_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aianalysisrequest",
            index=models.Index(
                fields=["analysis_type", "-created_at"],
                name="ai_services_analysi_e1015f_idx",
            ),
        ),
    ]
