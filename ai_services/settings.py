"""
Settings for AI services.

This module contains settings that control the behavior of AI services.
These settings can be overridden in the main Django settings.py file.
"""

from django.conf import settings

# Whether AI features are enabled
ENABLE_AI_FEATURES = getattr(settings, 'ENABLE_AI_FEATURES', True)

# Default model to use
DEFAULT_MODEL_NAME = getattr(settings, 'DEFAULT_LLM_MODEL', 'gemma-3-12b-it-qat')

# Default endpoint URL for LLM API
DEFAULT_LLM_ENDPOINT = getattr(settings, 'DEFAULT_LLM_ENDPOINT', 'http://127.0.0.1:1234/v1/completions')

# Default endpoint URL for embeddings API
DEFAULT_EMBEDDING_ENDPOINT = getattr(settings, 'DEFAULT_EMBEDDING_ENDPOINT', 'http://127.0.0.1:1234/v1/embeddings')

# Whether to use mock services as fallback
USE_MOCK_FALLBACK = getattr(settings, 'USE_MOCK_FALLBACK', True)

# Maximum timeout for LLM API requests (in seconds)
LLM_REQUEST_TIMEOUT = getattr(settings, 'LLM_REQUEST_TIMEOUT', 60)

# Maximum tokens to generate
DEFAULT_MAX_TOKENS = getattr(settings, 'DEFAULT_MAX_TOKENS', 4096)

# Default temperature for generation
DEFAULT_TEMPERATURE = getattr(settings, 'DEFAULT_TEMPERATURE', 0.7)

# Vector dimensions for embeddings
DEFAULT_VECTOR_DIMENSIONS = getattr(settings, 'DEFAULT_VECTOR_DIMENSIONS', 768)
