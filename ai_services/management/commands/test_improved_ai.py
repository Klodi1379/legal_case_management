import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ai_services.models import LLMModel, PromptTemplate, VectorStore
from ai_services.services.service_factory import AIServiceFactory

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tests the improved AI services integration'

    def add_arguments(self, parser):
        parser.add_argument('--prompt', type=str, help='Prompt to send to Gemma 3')
        parser.add_argument('--model_id', type=int, help='ID of the LLM model to use')
        parser.add_argument('--no-fallback', action='store_true', help='Disable mock fallback')

    def handle(self, *args, **options):
        self.stdout.write('Testing improved AI services...')
        
        prompt = options.get('prompt')
        model_id = options.get('model_id')
        use_fallback = not options.get('no_fallback', False)
        
        if not prompt:
            prompt = "Explain the key components of a legal case management system."
        
        try:
            # Get the model
            if model_id:
                model = LLMModel.objects.get(id=model_id)
            else:
                model = LLMModel.objects.filter(is_active=True).first()
                
            if not model:
                self.stdout.write(self.style.ERROR('No active LLM models found.'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Using model: {model.name}'))
            self.stdout.write(f'Model endpoint: {model.endpoint_url}')
            self.stdout.write(f'Mock fallback: {"Enabled" if use_fallback else "Disabled"}')
            
            # Create the service using the factory
            service = AIServiceFactory.get_llm_service(model, use_mock_fallback=use_fallback)
            
            # Generate text
            self.stdout.write(self.style.WARNING('Sending prompt to Gemma 3...'))
            self.stdout.write(f'Prompt: {prompt}')
            
            import time
            start_time = time.time()
            result = service.generate_text(prompt=prompt)
            end_time = time.time()
            
            if result.get('error'):
                self.stdout.write(self.style.ERROR(f'Error: {result["error"]}'))
                return
            
            # Display the result
            self.stdout.write(self.style.SUCCESS('Response received!'))
            self.stdout.write(f'Processing time: {result["processing_time"]:.2f} seconds')
            self.stdout.write(f'Tokens used: {result["tokens_used"]}')
            self.stdout.write(f'Response:')
            self.stdout.write(result['text'])
            
            # Check if mock service was used
            if 'raw_response' in result and isinstance(result['raw_response'], dict):
                if result['raw_response'].get('mock_response', False):
                    self.stdout.write(self.style.WARNING('Note: Mock service was used to generate this response.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing AI services: {str(e)}'))
            import traceback
            traceback.print_exc()
            
        self.stdout.write(self.style.SUCCESS('AI services test complete!'))
