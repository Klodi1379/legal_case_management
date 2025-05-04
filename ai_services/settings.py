"""
Settings for AI services.

This module contains settings that control the behavior of AI services.
These settings can be overridden in the main Django settings.py file
or loaded from the database.
"""

import os
from django.conf import settings

# Feature flags
ENABLE_AI_FEATURES = getattr(settings, 'ENABLE_AI_FEATURES', True)
ENABLE_VECTOR_SEARCH = getattr(settings, 'ENABLE_VECTOR_SEARCH', True)
ENABLE_DOCUMENT_GENERATION = getattr(settings, 'ENABLE_DOCUMENT_GENERATION', True)
ENABLE_LEGAL_RESEARCH = getattr(settings, 'ENABLE_LEGAL_RESEARCH', True)

# Default model settings
DEFAULT_MODEL_NAME = getattr(settings, 'DEFAULT_LLM_MODEL', 'gemma-3-12b-it-qat')
DEFAULT_LLM_ENDPOINT = getattr(settings, 'DEFAULT_LLM_ENDPOINT', 'http://127.0.0.1:1234/v1/chat/completions')
DEFAULT_EMBEDDING_MODEL = getattr(settings, 'DEFAULT_EMBEDDING_MODEL', 'gemma-3-embedding')
DEFAULT_EMBEDDING_ENDPOINT = getattr(settings, 'DEFAULT_EMBEDDING_ENDPOINT', 'http://127.0.0.1:1234/v1/embeddings')

# Fallback and error handling
USE_MOCK_FALLBACK = getattr(settings, 'USE_MOCK_FALLBACK', True)
MAX_RETRY_ATTEMPTS = getattr(settings, 'MAX_RETRY_ATTEMPTS', 3)
RETRY_INITIAL_DELAY = getattr(settings, 'RETRY_INITIAL_DELAY', 1.0)
RETRY_MAX_DELAY = getattr(settings, 'RETRY_MAX_DELAY', 10.0)
RETRY_BACKOFF_FACTOR = getattr(settings, 'RETRY_BACKOFF_FACTOR', 2.0)
RETRY_JITTER = getattr(settings, 'RETRY_JITTER', True)

# Service monitoring
ENABLE_SERVICE_MONITORING = getattr(settings, 'ENABLE_SERVICE_MONITORING', True)
SERVICE_HEALTH_CACHE_EXPIRY = getattr(settings, 'SERVICE_HEALTH_CACHE_EXPIRY', 300)  # 5 minutes
SERVICE_HEALTH_CHECK_INTERVAL = getattr(settings, 'SERVICE_HEALTH_CHECK_INTERVAL', 60)  # 1 minute

# Request settings
LLM_REQUEST_TIMEOUT = getattr(settings, 'LLM_REQUEST_TIMEOUT', 60)
DEFAULT_MAX_TOKENS = getattr(settings, 'DEFAULT_MAX_TOKENS', 4096)
DEFAULT_TEMPERATURE = getattr(settings, 'DEFAULT_TEMPERATURE', 0.7)

# Vector search settings
DEFAULT_VECTOR_DIMENSIONS = getattr(settings, 'DEFAULT_VECTOR_DIMENSIONS', 768)
VECTOR_SEARCH_TOP_K = getattr(settings, 'VECTOR_SEARCH_TOP_K', 5)
VECTOR_SEARCH_THRESHOLD = getattr(settings, 'VECTOR_SEARCH_THRESHOLD', 0.7)

# Document processing settings
MAX_DOCUMENT_SIZE = getattr(settings, 'MAX_DOCUMENT_SIZE', 10 * 1024 * 1024)  # 10MB
SUPPORTED_DOCUMENT_TYPES = getattr(settings, 'SUPPORTED_DOCUMENT_TYPES',
                                  ['.pdf', '.docx', '.doc', '.txt', '.md'])

# System prompts
DEFAULT_SYSTEM_PROMPT = getattr(settings, 'DEFAULT_SYSTEM_PROMPT', """
You are a legal assistant AI helping with legal tasks.
Provide accurate, professional responses based on the information provided.
Always maintain attorney-client privilege and confidentiality.
If you're unsure about something, acknowledge the limitations of your knowledge.
""")

DOCUMENT_ANALYSIS_SYSTEM_PROMPT = getattr(settings, 'DOCUMENT_ANALYSIS_SYSTEM_PROMPT', """
You are a legal document analysis assistant.
Analyze the provided document carefully and provide insights based on legal principles.
Focus on identifying key legal issues, potential risks, and important clauses.
Maintain a professional tone and be precise in your analysis.
""")

LEGAL_RESEARCH_SYSTEM_PROMPT = getattr(settings, 'LEGAL_RESEARCH_SYSTEM_PROMPT', """
You are a legal research assistant.
Provide thorough research on the legal question presented.
Cite relevant cases, statutes, and legal principles.
Present balanced viewpoints and acknowledge areas of legal uncertainty.
""")

# Load settings from database
def get_setting(key, default=None):
    """
    Get a setting from the database or fall back to default.

    Args:
        key: Setting key
        default: Default value if setting not found

    Returns:
        Setting value
    """
    try:
        from .models import AISettings
        setting = AISettings.objects.filter(key=key).first()
        if setting:
            return setting.value
    except:
        pass
    return default

def load_settings():
    """
    Load settings from the database.

    This function is called during app initialization to override
    default settings with values from the database.
    """
    global DEFAULT_MODEL_NAME, DEFAULT_LLM_ENDPOINT, DEFAULT_SYSTEM_PROMPT
    global ENABLE_VECTOR_SEARCH, ENABLE_DOCUMENT_GENERATION, ENABLE_LEGAL_RESEARCH
    global MAX_RETRY_ATTEMPTS, RETRY_INITIAL_DELAY, RETRY_MAX_DELAY, RETRY_BACKOFF_FACTOR
    global ENABLE_SERVICE_MONITORING

    try:
        # Only try to load settings if the database is available
        from django.db import connection
        if connection.is_usable():
            DEFAULT_MODEL_NAME = get_setting('DEFAULT_MODEL_NAME', DEFAULT_MODEL_NAME)
            DEFAULT_LLM_ENDPOINT = get_setting('DEFAULT_LLM_ENDPOINT', DEFAULT_LLM_ENDPOINT)
            DEFAULT_SYSTEM_PROMPT = get_setting('DEFAULT_SYSTEM_PROMPT', DEFAULT_SYSTEM_PROMPT)

            # Feature flags
            enable_vector_search = get_setting('ENABLE_VECTOR_SEARCH')
            if enable_vector_search is not None:
                ENABLE_VECTOR_SEARCH = enable_vector_search.lower() == 'true'

            enable_document_generation = get_setting('ENABLE_DOCUMENT_GENERATION')
            if enable_document_generation is not None:
                ENABLE_DOCUMENT_GENERATION = enable_document_generation.lower() == 'true'

            enable_legal_research = get_setting('ENABLE_LEGAL_RESEARCH')
            if enable_legal_research is not None:
                ENABLE_LEGAL_RESEARCH = enable_legal_research.lower() == 'true'

            # Retry settings
            max_retry_attempts = get_setting('MAX_RETRY_ATTEMPTS')
            if max_retry_attempts is not None:
                try:
                    MAX_RETRY_ATTEMPTS = int(max_retry_attempts)
                except ValueError:
                    pass

            retry_initial_delay = get_setting('RETRY_INITIAL_DELAY')
            if retry_initial_delay is not None:
                try:
                    RETRY_INITIAL_DELAY = float(retry_initial_delay)
                except ValueError:
                    pass

            # Service monitoring
            enable_service_monitoring = get_setting('ENABLE_SERVICE_MONITORING')
            if enable_service_monitoring is not None:
                ENABLE_SERVICE_MONITORING = enable_service_monitoring.lower() == 'true'
    except:
        # If there's any error, just use the default settings
        pass
