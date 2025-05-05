import logging
import json
import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ai_services.models import LLMModel, PromptTemplate, VectorStore
from ai_services.services.service_factory import AIServiceFactory
from ai_services.services.service_monitor import ServiceMonitor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tests the improved AI services integration'

    def add_arguments(self, parser):
        parser.add_argument('--prompt', type=str, help='Prompt to send to Gemma 3')
        parser.add_argument('--model_id', type=int, help='ID of the LLM model to use')
        parser.add_argument('--no-fallback', action='store_true', help='Disable mock fallback')
        parser.add_argument('--health-check', action='store_true', help='Run a health check on all services')
        parser.add_argument('--system-prompt', type=str, help='System prompt to use')

    def handle(self, *args, **options):
        self.stdout.write('Testing improved AI services...')

        # Check if we should run a health check
        if options.get('health_check'):
            self.run_health_check()
            return

        prompt = options.get('prompt')
        model_id = options.get('model_id')
        use_fallback = not options.get('no_fallback', False)
        system_prompt = options.get('system_prompt')

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
            self.stdout.write(f'Model type: {model.get_model_type_display()}')
            self.stdout.write(f'Model version: {model.model_version}')
            self.stdout.write(f'Deployment type: {model.get_deployment_type_display()}')
            self.stdout.write(f'Model endpoint: {model.endpoint_url}')
            self.stdout.write(f'Mock fallback: {"Enabled" if use_fallback else "Disabled"}')

            # Check service health
            self.stdout.write(self.style.WARNING('Checking service health...'))
            is_healthy = AIServiceFactory._is_service_healthy("GemmaService", model.endpoint_url)
            if is_healthy:
                self.stdout.write(self.style.SUCCESS('Service health check passed!'))
            else:
                self.stdout.write(self.style.ERROR('Service health check failed!'))
                if not use_fallback:
                    self.stdout.write(self.style.WARNING('Continuing anyway since fallback is disabled...'))

            # Create the service using the factory
            service = AIServiceFactory.get_llm_service(model, use_mock_fallback=use_fallback)

            # Generate text
            self.stdout.write(self.style.WARNING('Sending prompt to Gemma 3...'))
            self.stdout.write(f'Prompt: {prompt}')
            if system_prompt:
                self.stdout.write(f'System prompt: {system_prompt}')

            self.stdout.write(self.style.WARNING('Generating response... (this may take a while without GPU)'))
            start_time = time.time()
            result = service.generate_text(prompt=prompt, system_prompt=system_prompt)
            end_time = time.time()

            if result.get('error'):
                error_message = result["error"]
                self.stdout.write(self.style.ERROR(f'Error: {error_message}'))

                # Provide helpful information for specific errors
                if "Model unloaded" in error_message:
                    self.stdout.write(self.style.WARNING("The model was unloaded in LM Studio. This can happen when:"))
                    self.stdout.write(self.style.WARNING("1. The model has not been used for a while"))
                    self.stdout.write(self.style.WARNING("2. LM Studio is conserving memory resources"))
                    self.stdout.write(self.style.WARNING("3. The model was manually unloaded"))
                    self.stdout.write(self.style.WARNING("\nTo fix this issue:"))
                    self.stdout.write(self.style.WARNING("1. Go to LM Studio and reload the model"))
                    self.stdout.write(self.style.WARNING("2. Restart the LM Studio server"))
                    self.stdout.write(self.style.WARNING("3. Try a different model"))
                elif "'messages' field is required" in error_message:
                    self.stdout.write(self.style.WARNING("There's an issue with the API request format:"))
                    self.stdout.write(self.style.WARNING("1. Make sure you're using the correct endpoint URL"))
                    self.stdout.write(self.style.WARNING("2. For chat completions, use: http://127.0.0.1:1234/v1/chat/completions"))
                    self.stdout.write(self.style.WARNING("3. For text completions, use: http://127.0.0.1:1234/v1/completions"))
                    self.stdout.write(self.style.WARNING("4. Check that the model is properly loaded in LM Studio"))
                elif "Read timed out" in error_message or "timed out" in error_message.lower():
                    self.stdout.write(self.style.WARNING("The request to the LLM model timed out. This can happen when:"))
                    self.stdout.write(self.style.WARNING("1. The model is running on a CPU instead of a GPU (much slower)"))
                    self.stdout.write(self.style.WARNING("2. The model is processing a complex request"))
                    self.stdout.write(self.style.WARNING("3. The system is under heavy load"))
                    self.stdout.write(self.style.WARNING("\nTo fix this issue:"))
                    self.stdout.write(self.style.WARNING("1. Try a shorter prompt"))
                    self.stdout.write(self.style.WARNING("2. Reduce the max_tokens parameter"))
                    self.stdout.write(self.style.WARNING("3. Try a smaller model (e.g., Qwen3 4B instead of Gemma 3 12B)"))
                    self.stdout.write(self.style.WARNING("4. Increase the timeout setting in ai_services/settings.py"))

                return

            # Display the result
            self.stdout.write(self.style.SUCCESS('Response received!'))
            self.stdout.write(f'Processing time: {result["processing_time"]:.2f} seconds')
            self.stdout.write(f'Tokens used: {result["tokens_used"]}')

            # Check if mock service was used
            if result.get('used_fallback') or (
                'raw_response' in result and
                isinstance(result['raw_response'], dict) and
                result['raw_response'].get('mock_response', False)
            ):
                self.stdout.write(self.style.WARNING('⚠️ MOCK SERVICE WAS USED TO GENERATE THIS RESPONSE ⚠️'))
                if result.get('original_error'):
                    self.stdout.write(self.style.ERROR(f'Original error: {result["original_error"]}'))
            else:
                self.stdout.write(self.style.SUCCESS('✓ Real Gemma 3 service was used'))

            self.stdout.write(self.style.SUCCESS('Response:'))
            self.stdout.write('=' * 80)
            self.stdout.write(result['text'])
            self.stdout.write('=' * 80)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing AI services: {str(e)}'))
            import traceback
            traceback.print_exc()

        self.stdout.write(self.style.SUCCESS('AI services test complete!'))

    def run_health_check(self):
        """Run a health check on all services."""
        self.stdout.write(self.style.WARNING('Running health check on all services...'))

        # Check LLM models
        models = LLMModel.objects.all()
        self.stdout.write(f'Found {models.count()} LLM models')

        for model in models:
            self.stdout.write(f'\nChecking model: {model.name}')
            self.stdout.write(f'Endpoint: {model.endpoint_url}')

            # Check service health
            is_healthy = AIServiceFactory._is_service_healthy("GemmaService", model.endpoint_url)
            if is_healthy:
                self.stdout.write(self.style.SUCCESS('✓ Service health check passed!'))
            else:
                self.stdout.write(self.style.ERROR('✗ Service health check failed!'))

            # Get service health from monitor
            health = ServiceMonitor.get_service_health("GemmaService")
            self.stdout.write(f'Service status: {health.get("status", "unknown")}')

            if "success_rate" in health:
                self.stdout.write(f'Success rate: {health["success_rate"]:.2f}%')
            else:
                self.stdout.write(f'Success rate: N/A')

            if "avg_response_time" in health:
                self.stdout.write(f'Average response time: {health["avg_response_time"]:.2f}s')
            else:
                self.stdout.write(f'Average response time: N/A')

            # Try a quick test
            try:
                service = AIServiceFactory.get_llm_service(model, use_mock_fallback=False, check_health=False)
                self.stdout.write(self.style.WARNING('Running quick test... (this may take a while without GPU)'))
                start_time = time.time()
                result = service.generate_text(
                    prompt="This is a quick test. Please respond with 'Service is working'.",
                    system_prompt="You are a helpful assistant."
                )
                end_time = time.time()

                if result.get('error'):
                    error_message = result["error"]
                    self.stdout.write(self.style.ERROR(f'✗ Test failed: {error_message}'))

                    # Provide helpful information for specific errors
                    if "Model unloaded" in error_message:
                        self.stdout.write(self.style.WARNING("The model was unloaded in LM Studio. Try reloading it."))
                    elif "'messages' field is required" in error_message:
                        self.stdout.write(self.style.WARNING("API format issue. Check endpoint URL and model configuration."))
                    elif "Read timed out" in error_message or "timed out" in error_message.lower():
                        self.stdout.write(self.style.WARNING("Request timed out. Try a smaller model or shorter prompt."))
                else:
                    self.stdout.write(self.style.SUCCESS('✓ Test passed!'))
                    self.stdout.write(f'Response time: {end_time - start_time:.2f}s')
                    self.stdout.write(f'Response: {result["text"][:50]}...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Test failed with exception: {str(e)}'))

        # Check vector stores
        vector_stores = VectorStore.objects.all()
        self.stdout.write(f'\nFound {vector_stores.count()} vector stores')

        for store in vector_stores:
            self.stdout.write(f'\nChecking vector store: {store.name}')
            self.stdout.write(f'Connection: {store.connection_string}')

            # Check service health
            is_healthy = AIServiceFactory._is_service_healthy("VectorSearchService", store.connection_string)
            if is_healthy:
                self.stdout.write(self.style.SUCCESS('✓ Service health check passed!'))
            else:
                self.stdout.write(self.style.ERROR('✗ Service health check failed!'))

        self.stdout.write(self.style.SUCCESS('\nHealth check complete!'))
