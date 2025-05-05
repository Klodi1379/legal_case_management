"""
AI Service Factory for creating AI service instances based on configuration.
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from ..models import LLMModel
from ..providers.factory import AIProviderFactory
from .base import BaseAIService, LLMService, MockLLMService
from .llm_service import LLMService as DefaultLLMService

logger = logging.getLogger(__name__)


class AIServiceFactory:
    """
    Factory for creating AI service instances based on configuration.
    """
    
    @classmethod
    def create_llm_service(cls, model_id: Optional[int] = None) -> LLMService:
        """
        Create an LLM service instance based on model configuration.
        
        Args:
            model_id: ID of the LLM model to use
            
        Returns:
            LLM service instance
        """
        # Check if AI features are enabled
        if not getattr(settings, 'ENABLE_AI_FEATURES', True):
            logger.info("AI features are disabled, returning mock service")
            return MockLLMService()
        
        try:
            # Get model configuration
            if model_id:
                model = LLMModel.objects.filter(id=model_id, is_active=True).first()
            else:
                # Get the default active model
                model = LLMModel.objects.filter(is_active=True).first()
            
            if not model:
                logger.warning("No active LLM model found, using mock service")
                return MockLLMService()
            
            # Create provider based on model configuration
            model_config = {
                'model_type': model.model_type,
                'model_version': model.model_version,
                'deployment_type': model.deployment_type,
                'endpoint_url': model.endpoint_url,
                'api_key': model.api_key,
                'api_key_name': model.api_key_name,
                'organization_id': model.organization_id,
                'max_tokens': model.max_tokens,
                'temperature': model.temperature,
                'top_p': model.top_p,
                'frequency_penalty': model.frequency_penalty,
                'presence_penalty': model.presence_penalty,
            }
            
            provider = AIProviderFactory.create_provider(model_config)
            
            if not provider:
                logger.warning(f"Failed to create provider for model {model.name}, using mock service")
                return MockLLMService()
            
            # Create and return the service with the provider
            service = DefaultLLMService()
            service.provider = provider
            service.model = model
            return service
            
        except Exception as e:
            logger.error(f"Error creating LLM service: {str(e)}")
            return MockLLMService()
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Any]:
        """
        Get information about available models and their status.
        
        Returns:
            Dictionary with model information
        """
        models = LLMModel.objects.filter(is_active=True)
        available_models = []
        
        for model in models:
            model_info = {
                'id': model.id,
                'name': model.name,
                'type': model.model_type,
                'version': model.model_version,
                'deployment_type': model.deployment_type,
                'is_free': model.is_free,
                'cost_per_1k_tokens': float(model.cost_per_1k_tokens) if model.cost_per_1k_tokens else None,
            }
            
            # Check if the model is available
            model_config = {
                'model_type': model.model_type,
                'model_version': model.model_version,
                'deployment_type': model.deployment_type,
                'endpoint_url': model.endpoint_url,
                'api_key': model.api_key,
                'api_key_name': model.api_key_name,
            }
            
            provider = AIProviderFactory.create_provider(model_config)
            if provider:
                model_info['is_available'] = provider.is_available()
                model_info['supported_models'] = provider.get_supported_models()
            else:
                model_info['is_available'] = False
                model_info['supported_models'] = []
            
            available_models.append(model_info)
        
        return {
            'models': available_models,
            'ai_enabled': getattr(settings, 'ENABLE_AI_FEATURES', True),
            'providers': AIProviderFactory.get_supported_providers(),
        }
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported providers.
        
        Returns:
            Dictionary with provider information
        """
        providers = {}
        for provider_type in AIProviderFactory.get_supported_providers():
            providers[provider_type] = AIProviderFactory.get_provider_info(provider_type)
        
        return providers
