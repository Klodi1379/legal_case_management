"""
AI Provider Factory for creating appropriate provider instances.
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseAIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider
from .groq_provider import GroqProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """
    Factory class for creating AI provider instances based on model configuration.
    """
    
    _providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'openrouter': OpenRouterProvider,
        'ollama': OllamaProvider,
        'groq': GroqProvider,
    }
    
    @classmethod
    def create_provider(cls, model_config: Dict[str, Any]) -> Optional[BaseAIProvider]:
        """
        Create an appropriate AI provider instance based on model configuration.
        
        Args:
            model_config: Dictionary containing model configuration
            
        Returns:
            AI provider instance or None if provider type is not supported
        """
        provider_type = model_config.get('model_type', '').lower()
        
        # Map specific model types to general provider types
        provider_mapping = {
            'gemma_3': 'ollama',
            'gemma_2': 'ollama',
            'llama_3': 'ollama',
            'mistral': 'ollama',
            'gpt4free': 'openai',  # GPT4Free mimics OpenAI API
        }
        
        if provider_type in provider_mapping:
            provider_type = provider_mapping[provider_type]
        
        provider_class = cls._providers.get(provider_type)
        
        if not provider_class:
            logger.error(f"Unsupported provider type: {provider_type}")
            return None
        
        try:
            return provider_class(model_config)
        except Exception as e:
            logger.error(f"Failed to create provider instance: {str(e)}")
            return None
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Get list of supported provider types.
        
        Returns:
            List of supported provider names
        """
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls, provider_type: str) -> Dict[str, Any]:
        """
        Get information about a specific provider.
        
        Args:
            provider_type: Provider type name
            
        Returns:
            Dictionary containing provider information
        """
        provider_info = {
            'openai': {
                'name': 'OpenAI',
                'description': 'OpenAI API for GPT models',
                'requires_api_key': True,
                'supports_embeddings': True,
                'default_models': ['gpt-3.5-turbo', 'gpt-4'],
            },
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Anthropic API for Claude models',
                'requires_api_key': True,
                'supports_embeddings': False,
                'default_models': ['claude-3-sonnet', 'claude-3-opus'],
            },
            'openrouter': {
                'name': 'OpenRouter',
                'description': 'Unified API for multiple LLM providers',
                'requires_api_key': True,
                'supports_embeddings': False,
                'default_models': ['openai/gpt-3.5-turbo', 'anthropic/claude-3-sonnet'],
            },
            'ollama': {
                'name': 'Ollama',
                'description': 'Local model deployment with Ollama',
                'requires_api_key': False,
                'supports_embeddings': True,
                'default_models': ['llama2', 'mistral', 'gemma'],
            },
            'groq': {
                'name': 'Groq',
                'description': 'Groq API for fast inference',
                'requires_api_key': True,
                'supports_embeddings': False,
                'default_models': ['mixtral-8x7b-32768', 'llama2-70b-4096'],
            },
        }
        
        return provider_info.get(provider_type, {})
