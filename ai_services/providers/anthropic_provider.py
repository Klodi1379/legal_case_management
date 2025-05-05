"""
Anthropic (Claude) provider implementation.
"""
import requests
import logging
from typing import Dict, Any, List
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic API provider implementation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.endpoint_url = self.endpoint_url or "https://api.anthropic.com/v1/messages"
        
        # Default model name if not specified
        if not self.model_name:
            self.model_name = "claude-3-sonnet-20240229"
        
        # Anthropic API version
        self.api_version = "2023-06-01"
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to Anthropic.
        """
        headers = self.prepare_headers()
        headers['anthropic-version'] = self.api_version
        headers['x-api-key'] = self.api_key  # Anthropic uses x-api-key
        del headers['Authorization']  # Remove Authorization header
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None
        
        for message in messages:
            if message['role'] == 'system':
                system_message = message['content']
            else:
                anthropic_messages.append({
                    'role': message['role'] if message['role'] in ['user', 'assistant'] else 'user',
                    'content': message['content']
                })
        
        payload = {
            "model": self.model_name,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
        }
        
        if system_message:
            payload['system'] = system_message
        
        # Add other parameters if provided
        if self.top_p is not None:
            payload['top_p'] = self.top_p
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Convert Anthropic response to OpenAI format for compatibility
            anthropic_response = response.json()
            openai_format_response = {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': anthropic_response.get('content', [{}])[0].get('text', '')
                    },
                    'finish_reason': anthropic_response.get('stop_reason', 'stop')
                }],
                'usage': anthropic_response.get('usage', {})
            }
            
            return openai_format_response
        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic API request failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Anthropic doesn't provide embeddings API, so we'll return a placeholder.
        """
        logger.warning("Anthropic doesn't provide embeddings API")
        # Return a dummy embedding vector
        return [0.0] * 768
    
    def is_available(self) -> bool:
        """
        Check if Anthropic API is available.
        """
        if not self.api_key:
            return False
        
        try:
            # Test with a simple models endpoint
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': self.api_version,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers=headers,
                timeout=10
            )
            return response.status_code in [200, 404]  # 404 is expected for this endpoint
        except:
            return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported Anthropic models.
        """
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
