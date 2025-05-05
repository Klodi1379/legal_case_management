"""
LLM Service implementation using provider pattern.
"""
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from .base import LLMService
from ..models import LLMModel
from ..providers.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class LLMService(LLMService):
    """
    LLM service implementation using the provider pattern.
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.provider = None
        self.model = None
    
    def _ensure_provider(self) -> bool:
        """
        Ensure a provider is available for API calls.
        
        Returns:
            Boolean indicating if a provider is available
        """
        if self.provider:
            return True
        
        # Try to get default model and create provider
        try:
            model = LLMModel.objects.filter(is_active=True).first()
            if not model:
                logger.error("No active LLM model found")
                return False
            
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
            
            self.provider = AIProviderFactory.create_provider(model_config)
            self.model = model
            
            return self.provider is not None
        except Exception as e:
            logger.error(f"Failed to create provider: {str(e)}")
            return False
    
    def generate_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Generate a completion for the given prompt.
        """
        if not self._ensure_provider():
            return "AI service is currently unavailable."
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.provider.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return self.provider.extract_text_from_response(response)
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Generate a chat completion for the given messages.
        """
        if not self._ensure_provider():
            return "AI service is currently unavailable."
        
        try:
            response = self.provider.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return self.provider.extract_text_from_response(response)
        except Exception as e:
            logger.error(f"Error generating chat completion: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        """
        if not self._ensure_provider():
            return []
        
        try:
            return self.provider.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
    
    def is_available(self) -> bool:
        """
        Check if the LLM service is available.
        """
        if not self._ensure_provider():
            return False
        
        return self.provider.is_available()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        """
        if not self.model:
            return {"status": "No model configured"}
        
        return {
            "name": self.model.name,
            "type": self.model.model_type,
            "version": self.model.model_version,
            "deployment_type": self.model.deployment_type,
            "is_active": self.model.is_active,
            "is_free": self.model.is_free,
            "max_tokens": self.model.max_tokens,
        }
