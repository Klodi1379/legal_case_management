"""
Ollama provider implementation for local models.
"""
import requests
import logging
from typing import Dict, Any, List
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """
    Ollama local model provider implementation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.endpoint_url = self.endpoint_url or "http://localhost:11434/api/chat"
        self.generate_url = "http://localhost:11434/api/generate"
        self.embedding_url = "http://localhost:11434/api/embeddings"
        
        # Default model name if not specified
        if not self.model_name:
            self.model_name = "llama2"
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to Ollama.
        """
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', self.top_p),
                "num_predict": kwargs.get('max_tokens', self.max_tokens),
            }
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=120  # Longer timeout for local models
            )
            response.raise_for_status()
            
            # Convert Ollama response to OpenAI format for compatibility
            ollama_response = response.json()
            openai_format_response = {
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': ollama_response.get('message', {}).get('content', '')
                    },
                    'finish_reason': 'stop'
                }],
                'usage': {
                    'prompt_tokens': ollama_response.get('prompt_eval_count', 0),
                    'completion_tokens': ollama_response.get('eval_count', 0),
                    'total_tokens': ollama_response.get('prompt_eval_count', 0) + ollama_response.get('eval_count', 0)
                }
            }
            
            return openai_format_response
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings using Ollama.
        """
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        try:
            response = requests.post(
                self.embedding_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            if 'embedding' in result:
                return result['embedding']
            
            raise ValueError("No embedding data in response")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama embedding request failed: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available.
        """
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of models available in Ollama.
        """
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        
        # Return common models if API call fails
        return [
            "llama2",
            "mistral",
            "codellama",
            "gemma:7b",
            "mixtral",
            "neural-chat",
            "starling-lm",
            "vicuna",
        ]
