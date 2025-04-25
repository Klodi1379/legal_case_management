import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ai_services.models import LLMModel, PromptTemplate, VectorStore

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sets up default AI services configuration'

    def handle(self, *args, **options):
        self.stdout.write('Setting up AI services...')
        
        # Create default LLM model for Gemma 3
        self.setup_default_llm_model()
        
        # Create default vector store
        self.setup_default_vector_store()
        
        # Create default prompt templates
        self.setup_default_prompt_templates()
        
        self.stdout.write(self.style.SUCCESS('AI services setup complete!'))
    
    def setup_default_llm_model(self):
        """Create a default LLM model for Gemma 3 with LM Studio."""
        if not LLMModel.objects.filter(name='Gemma 3 (LM Studio)').exists():
            model = LLMModel.objects.create(
                name='Gemma 3 (LM Studio)',
                model_type='gemma_3',
                model_version='3-12b-it-qat',  # Using the correct model version
                deployment_type='api',
                endpoint_url='http://127.0.0.1:1234/v1/completions',
                quantization='4bit',
                max_tokens=4096,
                temperature=0.7,
                is_active=True
            )
            self.stdout.write(f'Created default LLM model: {model.name}')
        else:
            # Update existing model to ensure it has the correct settings
            model = LLMModel.objects.get(name='Gemma 3 (LM Studio)')
            model.model_version = '3-12b-it-qat'  # Ensure correct model version
            model.endpoint_url = 'http://127.0.0.1:1234/v1/completions'  # Ensure correct endpoint
            model.save()
            self.stdout.write('Updated default LLM model settings')
    
    def setup_default_vector_store(self):
        """Create a default vector store configuration."""
        if not VectorStore.objects.filter(name='Default Vector Store').exists():
            vector_store = VectorStore.objects.create(
                name='Default Vector Store',
                store_type='pgvector',
                embedding_model='gemma-3-embedding',
                dimensions=768,
                is_active=True
            )
            self.stdout.write(f'Created default vector store: {vector_store.name}')
        else:
            self.stdout.write('Default vector store already exists')
    
    def setup_default_prompt_templates(self):
        """Create default prompt templates for common tasks."""
        # Document Analysis Template
        if not PromptTemplate.objects.filter(name='Document Analysis').exists():
            template = PromptTemplate.objects.create(
                name='Document Analysis',
                task_type='document_analysis',
                system_prompt='You are a legal assistant analyzing a document. Provide a detailed analysis of the document, including key provisions, potential issues, and recommendations.',
                template_text='Please analyze the following document:\n\n{document_text}\n\nProvide a detailed analysis including key provisions, potential issues, and recommendations.',
                is_active=True
            )
            self.stdout.write(f'Created document analysis template: {template.name}')
        
        # Contract Review Template
        if not PromptTemplate.objects.filter(name='Contract Review').exists():
            template = PromptTemplate.objects.create(
                name='Contract Review',
                task_type='contract_analysis',
                system_prompt='You are a legal assistant reviewing a contract. Identify key clauses, obligations, risks, and suggest improvements.',
                template_text='Please review the following contract:\n\n{document_text}\n\nIdentify key clauses, obligations, risks, and suggest improvements.',
                is_active=True
            )
            self.stdout.write(f'Created contract review template: {template.name}')
        
        # Legal Research Template
        if not PromptTemplate.objects.filter(name='Legal Research').exists():
            template = PromptTemplate.objects.create(
                name='Legal Research',
                task_type='legal_research',
                system_prompt='You are a legal researcher. Provide a comprehensive analysis of the legal question, citing relevant cases, statutes, and legal principles.',
                template_text='Research question: {research_question}\n\nJurisdiction: {jurisdiction}\n\nProvide a comprehensive analysis with relevant cases, statutes, and legal principles.',
                is_active=True
            )
            self.stdout.write(f'Created legal research template: {template.name}')
