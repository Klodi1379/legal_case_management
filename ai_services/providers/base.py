"""
Base provider class for AI services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """
    Abstract base class for AI service providers.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the provider with model configuration.
        
        Args:
            model_config: Configuration dictionary containing model settings
        """
        self.model_config = model_config
        self.api_key = model_config.get('api_key')
        self.endpoint_url = model_config.get('endpoint_url')
        self.model_name = model_config.get('model_version', '')
        self.max_tokens = model_config.get('max_tokens', 4096)
        self.temperature = model_config.get('temperature', 0.7)
        self.top_p = model_config.get('top_p', 1.0)
        self.frequency_penalty = model_config.get('frequency_penalty', 0.0)
        self.presence_penalty = model_config.get('presence_penalty', 0.0)
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters specific to the provider
            
        Returns:
            Dictionary containing the response from the AI model
        """
        pass
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of float values representing the embedding
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.
        
        Returns:
            Boolean indicating availability
        """
        pass
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for this provider.
        
        Returns:
            List of model names
        """
        return []
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate the response from the AI model.
        
        Args:
            response: Response dictionary from the AI model
            
        Returns:
            Boolean indicating if the response is valid
        """
        if not response:
            return False
        
        # Basic validation - can be overridden by specific providers
        if 'choices' in response and len(response['choices']) > 0:
            return True
        
        return False
    
    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from AI model response.
        
        Args:
            response: Response dictionary from the AI model
            
        Returns:
            Extracted text content
        """
        try:
            # Standard OpenAI-like response format
            if 'choices' in response and len(response['choices']) > 0:
                choice = response['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    return choice['message']['content']
                elif 'text' in choice:
                    return choice['text']
            
            # Fallback for other response formats
            if 'content' in response:
                return response['content']
            
            if 'text' in response:
                return response['text']
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from response: {str(e)}")
            return ""
    
    def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare headers for API requests.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            api_key_name = self.model_config.get('api_key_name', 'Authorization')
            if api_key_name.lower() == 'authorization':
                headers[api_key_name] = f"Bearer {self.api_key}"
            else:
                headers[api_key_name] = self.api_key
        
        return headers
