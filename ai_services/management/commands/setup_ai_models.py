"""
Management command to set up default AI models.
"""
from django.core.management.base import BaseCommand
from ai_services.models import LLMModel


class Command(BaseCommand):
    help = 'Set up default AI models for the system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default AI models...')
        
        # Free/Local models
        models = [
            {
                'name': 'Ollama Llama 2',
                'model_type': 'ollama',
                'model_version': 'llama2',
                'deployment_type': 'ollama',
                'endpoint_url': 'http://localhost:11434/api/chat',
                'api_key': '',
                'max_tokens': 4096,
                'temperature': 0.7,
                'is_active': True,
                'is_free': True,
                'cost_per_1k_tokens': 0.0,
            },
            {
                'name': 'Ollama Mistral',
                'model_type': 'ollama',
                'model_version': 'mistral',
                'deployment_type': 'ollama',
                'endpoint_url': 'http://localhost:11434/api/chat',
                'api_key': '',
                'max_tokens': 8192,
                'temperature': 0.7,
                'is_active': True,
                'is_free': True,
                'cost_per_1k_tokens': 0.0,
            },
            {
                'name': 'Ollama Gemma 7B',
                'model_type': 'ollama',
                'model_version': 'gemma:7b',
                'deployment_type': 'ollama',
                'endpoint_url': 'http://localhost:11434/api/chat',
                'api_key': '',
                'max_tokens': 8192,
                'temperature': 0.7,
                'is_active': True,
                'is_free': True,
                'cost_per_1k_tokens': 0.0,
            },
            # API-based models (need API keys)
            {
                'name': 'OpenAI GPT-3.5 Turbo',
                'model_type': 'openai',
                'model_version': 'gpt-3.5-turbo',
                'deployment_type': 'api',
                'endpoint_url': 'https://api.openai.com/v1/chat/completions',
                'api_key': '',  # User needs to add their API key
                'api_key_name': 'Authorization',
                'max_tokens': 4096,
                'temperature': 0.7,
                'is_active': False,  # Disabled by default
                'is_free': False,
                'cost_per_1k_tokens': 0.002,  # $0.002 per 1K tokens
            },
            {
                'name': 'OpenAI GPT-4',
                'model_type': 'openai',
                'model_version': 'gpt-4',
                'deployment_type': 'api',
                'endpoint_url': 'https://api.openai.com/v1/chat/completions',
                'api_key': '',  # User needs to add their API key
                'api_key_name': 'Authorization',
                'max_tokens': 8192,
                'temperature': 0.7,
                'is_active': False,  # Disabled by default
                'is_free': False,
                'cost_per_1k_tokens': 0.03,  # $0.03 per 1K tokens
            },
            {
                'name': 'Anthropic Claude 3 Sonnet',
                'model_type': 'anthropic',
                'model_version': 'claude-3-sonnet-20240229',
                'deployment_type': 'api',
                'endpoint_url': 'https://api.anthropic.com/v1/messages',
                'api_key': '',  # User needs to add their API key
                'api_key_name': 'x-api-key',
                'max_tokens': 4096,
                'temperature': 0.7,
                'is_active': False,  # Disabled by default
                'is_free': False,
                'cost_per_1k_tokens': 0.003,  # $0.003 per 1K tokens
            },
            {
                'name': 'Groq Mixtral 8x7B',
                'model_type': 'groq',
                'model_version': 'mixtral-8x7b-32768',
                'deployment_type': 'api',
                'endpoint_url': 'https://api.groq.com/openai/v1/chat/completions',
                'api_key': '',  # User needs to add their API key
                'api_key_name': 'Authorization',
                'max_tokens': 32768,
                'temperature': 0.7,
                'is_active': False,  # Disabled by default
                'is_free': False,
                'cost_per_1k_tokens': 0.00027,  # Very cheap!
            },
            {
                'name': 'OpenRouter GPT-3.5 Turbo',
                'model_type': 'openrouter',
                'model_version': 'openai/gpt-3.5-turbo',
                'deployment_type': 'api',
                'endpoint_url': 'https://openrouter.ai/api/v1/chat/completions',
                'api_key': '',  # User needs to add their API key
                'api_key_name': 'Authorization',
                'max_tokens': 4096,
                'temperature': 0.7,
                'is_active': False,  # Disabled by default
                'is_free': False,
                'cost_per_1k_tokens': 0.002,
            },
        ]
        
        for model_data in models:
            model, created = LLMModel.objects.update_or_create(
                name=model_data['name'],
                defaults=model_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created model: {model.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated model: {model.name}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully set up AI models!'))
        
        # Print instructions
        self.stdout.write('\nImportant Notes:')
        self.stdout.write('1. Local models (Ollama) are ready to use if you have Ollama installed and running')
        self.stdout.write('2. API-based models are disabled by default - you need to:')
        self.stdout.write('   - Add your API key in the admin panel')
        self.stdout.write('   - Enable the model by setting is_active=True')
        self.stdout.write('3. Some providers offer free tiers or trials:')
        self.stdout.write('   - OpenAI: Free trial credits for new accounts')
        self.stdout.write('   - Anthropic: Limited free access for developers')
        self.stdout.write('   - Groq: Very generous free tier')
        self.stdout.write('   - OpenRouter: Pay-as-you-go with many model options')
        self.stdout.write('\nVisit the admin panel to configure AI models!')
