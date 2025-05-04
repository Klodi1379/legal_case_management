import logging
import time
from typing import Union, Optional, Dict, Any, Type
from django.conf import settings
from django.utils import timezone
from .. import settings as ai_settings
from ..models import LLMModel, VectorStore, AISettings
from .exceptions import (
    AIServiceException, ServiceConnectionError, ServiceTimeoutError,
    ServiceResponseError, ServiceParsingError, ModelNotFoundError
)
from .service_monitor import ServiceMonitor
from .retry_utils import retry_with_exponential_backoff, RetryContext

logger = logging.getLogger(__name__)

class AIServiceFactory:
    """
    Factory class for creating AI service instances.

    This factory decides whether to use real or mock services based on configuration
    and availability of the real services. It includes enhanced error handling,
    retry logic, and service monitoring capabilities.
    """

    # Service health check cache
    _service_health_cache = {}
    _service_health_cache_time = {}

    # Cache expiration time (5 minutes)
    _HEALTH_CACHE_EXPIRY = 300

    @classmethod
    def get_llm_service(cls, model_instance: LLMModel, use_mock_fallback: bool = None,
                       max_retries: int = None, check_health: bool = True):
        """
        Get an LLM service instance.

        Args:
            model_instance: The LLM model configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            max_retries: Maximum number of retries for service calls
            check_health: Whether to check service health before returning

        Returns:
            An instance of GemmaService or MockGemmaService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES

        # Use settings values if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK

        if max_retries is None:
            max_retries = ai_settings.MAX_RETRY_ATTEMPTS

        # If AI features are disabled, return mock service
        if not ai_enabled:
            logger.info("AI features are disabled. Using mock service.")
            from .mock_llm_service import MockGemmaService
            return MockGemmaService(model_instance)

        # Check service health if requested
        if check_health and not cls._is_service_healthy("GemmaService", model_instance.endpoint_url):
            logger.warning(f"Service health check failed for {model_instance.name}. Using mock service.")
            from .mock_llm_service import MockGemmaService
            return MockGemmaService(model_instance)

        # Try to import and use the real service
        try:
            from .llm_service import GemmaService

            # If mock fallback is enabled, use a wrapper that will try real service first
            if use_mock_fallback:
                return cls._create_llm_service_with_fallback(model_instance, max_retries)

            # Otherwise, use the real service directly with retry decorator
            return cls._create_llm_service_with_retry(GemmaService, model_instance, max_retries)

        except ImportError as e:
            logger.warning(f"Could not import GemmaService: {str(e)}. Using mock service.")
            from .mock_llm_service import MockGemmaService
            return MockGemmaService(model_instance)

    @classmethod
    def _create_llm_service_with_fallback(cls, model_instance: LLMModel, max_retries: int = 3):
        """
        Create an LLM service with fallback to mock service.

        This creates a wrapper around the real service that will try the real service first,
        and if it fails, fall back to the mock service. It includes retry logic and
        service monitoring.

        Args:
            model_instance: The LLM model configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with fallback capability
        """
        from .llm_service import GemmaService
        from .mock_llm_service import MockGemmaService

        # Create the real service with retry capability
        real_service = cls._create_llm_service_with_retry(GemmaService, model_instance, max_retries)
        mock_service = MockGemmaService(model_instance)

        class LLMServiceWithFallback:
            """Wrapper class that tries real service first, then falls back to mock."""

            def __init__(self, real_service, mock_service, model):
                self.real_service = real_service
                self.mock_service = mock_service
                self.model = model
                self.service_name = "GemmaService"

            def generate_text(self, prompt, system_prompt=None, **kwargs):
                """Generate text with fallback to mock service if real service fails."""
                start_time = time.time()

                try:
                    logger.info(f"Attempting to use real LLM service with model {self.model.name}")
                    result = self.real_service.generate_text(prompt, system_prompt, **kwargs)

                    # Record successful service call
                    end_time = time.time()
                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.model.endpoint_url,
                        success=not bool(result.get("error")),
                        response_time=end_time - start_time,
                        error_type=None if not result.get("error") else "API_ERROR",
                        error_message=result.get("error")
                    )

                    # If there was an error, try the mock service
                    if result.get("error"):
                        logger.warning(f"Real LLM service returned error: {result['error']}. Falling back to mock service.")
                        mock_start_time = time.time()
                        mock_result = self.mock_service.generate_text(prompt, system_prompt, **kwargs)
                        mock_end_time = time.time()

                        # Add fallback indicator to result
                        mock_result["used_fallback"] = True
                        mock_result["original_error"] = result.get("error")

                        # Record mock service call
                        ServiceMonitor.record_service_call(
                            service_name="MockGemmaService",
                            endpoint="mock://local",
                            success=True,
                            response_time=mock_end_time - mock_start_time
                        )

                        return mock_result

                    return result

                except Exception as e:
                    # Record failed service call
                    end_time = time.time()
                    error_type = type(e).__name__
                    error_message = str(e)

                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.model.endpoint_url,
                        success=False,
                        response_time=end_time - start_time,
                        error_type=error_type,
                        error_message=error_message
                    )

                    logger.warning(f"Error using real LLM service: {error_message}. Falling back to mock service.")

                    # Use mock service as fallback
                    mock_start_time = time.time()
                    mock_result = self.mock_service.generate_text(prompt, system_prompt, **kwargs)
                    mock_end_time = time.time()

                    # Add fallback indicator to result
                    mock_result["used_fallback"] = True
                    mock_result["original_error"] = error_message

                    # Record mock service call
                    ServiceMonitor.record_service_call(
                        service_name="MockGemmaService",
                        endpoint="mock://local",
                        success=True,
                        response_time=mock_end_time - mock_start_time
                    )

                    return mock_result

            def process_analysis_request(self, request_id: int):
                """Process an analysis request with fallback capability."""
                start_time = time.time()

                try:
                    result = self.real_service.process_analysis_request(request_id)

                    # Record successful service call
                    end_time = time.time()
                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.model.endpoint_url,
                        success=True,
                        response_time=end_time - start_time
                    )

                    return result

                except Exception as e:
                    # Record failed service call
                    end_time = time.time()
                    error_type = type(e).__name__
                    error_message = str(e)

                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.model.endpoint_url,
                        success=False,
                        response_time=end_time - start_time,
                        error_type=error_type,
                        error_message=error_message
                    )

                    logger.warning(f"Error processing analysis with real service: {error_message}. Falling back to mock service.")

                    # Use mock service as fallback
                    return self.mock_service.process_analysis_request(request_id)

        return LLMServiceWithFallback(real_service, mock_service, model_instance)

    @classmethod
    def _create_llm_service_with_retry(cls, service_class, model_instance: LLMModel, max_retries: int = 3):
        """
        Create an LLM service with retry capability.

        This wraps the service methods with retry decorators to automatically
        retry failed operations with exponential backoff.

        Args:
            service_class: The service class to instantiate
            model_instance: The LLM model configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with retry capability
        """
        # Create the base service instance
        service = service_class(model_instance)

        # Create a wrapper class with retry capability
        class ServiceWithRetry:
            """Wrapper class that adds retry capability to service methods."""

            def __init__(self, service, model):
                self.service = service
                self.model = model
                self.service_name = service.__class__.__name__

            @retry_with_exponential_backoff(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            def generate_text(self, prompt, system_prompt=None, **kwargs):
                """Generate text with retry capability."""
                return self.service.generate_text(prompt, system_prompt, **kwargs)

            @retry_with_exponential_backoff(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            def process_analysis_request(self, request_id: int):
                """Process an analysis request with retry capability."""
                return self.service.process_analysis_request(request_id)

        return ServiceWithRetry(service, model_instance)

    @classmethod
    def _is_service_healthy(cls, service_name: str, endpoint: str) -> bool:
        """
        Check if a service is healthy.

        This method checks the cached health status of a service and
        returns whether it's considered healthy. If the health status
        is not cached or expired, it returns True to allow the service
        to be tried.

        Args:
            service_name: Name of the service
            endpoint: Service endpoint URL

        Returns:
            True if the service is healthy or unknown, False otherwise
        """
        # Check if we have a recent health check
        cache_key = f"{service_name}:{endpoint}"
        now = time.time()

        if cache_key in cls._service_health_cache_time:
            # Check if the cache is still valid
            if now - cls._service_health_cache_time[cache_key] < cls._HEALTH_CACHE_EXPIRY:
                # Return cached health status
                return cls._service_health_cache[cache_key]

        # Get current health status from monitor
        health = ServiceMonitor.get_service_health(service_name)

        # Consider the service unhealthy if it's in "unhealthy" status
        is_healthy = health["status"] != ServiceMonitor.STATUS_UNHEALTHY

        # Cache the result
        cls._service_health_cache[cache_key] = is_healthy
        cls._service_health_cache_time[cache_key] = now

        return is_healthy

    @classmethod
    def get_vector_search_service(cls, vector_store: VectorStore, use_mock_fallback: bool = None,
                                 max_retries: int = None, check_health: bool = True):
        """
        Get a vector search service instance.

        Args:
            vector_store: The vector store configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            max_retries: Maximum number of retries for service calls
            check_health: Whether to check service health before returning

        Returns:
            An instance of VectorSearchService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES

        # Use settings values if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK

        if max_retries is None:
            max_retries = ai_settings.MAX_RETRY_ATTEMPTS

        if not ai_enabled:
            logger.info("AI features are disabled. Using mock vector search service.")
            from .mock_vector_search import MockVectorSearchService
            return MockVectorSearchService(vector_store)

        # Check service health if requested
        if check_health and not cls._is_service_healthy("VectorSearchService", vector_store.connection_string):
            logger.warning(f"Service health check failed for vector search. Using mock service.")
            from .mock_vector_search import MockVectorSearchService
            return MockVectorSearchService(vector_store)

        # Try to import and use the real service
        try:
            from .vector_search import VectorSearchService

            # If mock fallback is enabled, create a wrapper with fallback
            if use_mock_fallback:
                return cls._create_vector_search_with_fallback(vector_store, max_retries)

            # Otherwise, use the real service with retry capability
            return cls._create_vector_search_with_retry(VectorSearchService, vector_store, max_retries)

        except ImportError as e:
            logger.warning(f"Could not import VectorSearchService: {str(e)}. Using mock service.")
            from .mock_vector_search import MockVectorSearchService
            return MockVectorSearchService(vector_store)

    @classmethod
    def get_embedding_service(cls, vector_store: VectorStore, use_mock_fallback: bool = None,
                             max_retries: int = None, check_health: bool = True):
        """
        Get an embedding service instance.

        Args:
            vector_store: The vector store configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            max_retries: Maximum number of retries for service calls
            check_health: Whether to check service health before returning

        Returns:
            An instance of EmbeddingService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES

        # Use settings values if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK

        if max_retries is None:
            max_retries = ai_settings.MAX_RETRY_ATTEMPTS

        if not ai_enabled:
            logger.info("AI features are disabled. Using mock embedding service.")
            from .mock_embedding_service import MockEmbeddingService
            return MockEmbeddingService(vector_store)

        # Check service health if requested
        if check_health and not cls._is_service_healthy("EmbeddingService", vector_store.connection_string):
            logger.warning(f"Service health check failed for embedding service. Using mock service.")
            from .mock_embedding_service import MockEmbeddingService
            return MockEmbeddingService(vector_store)

        # Try to import and use the real service
        try:
            from .embedding_service import EmbeddingService

            # If mock fallback is enabled, use a wrapper that will try real service first
            if use_mock_fallback:
                return cls._create_embedding_service_with_fallback(vector_store, max_retries)

            # Otherwise, use the real service with retry capability
            return cls._create_embedding_service_with_retry(EmbeddingService, vector_store, max_retries)

        except ImportError as e:
            logger.warning(f"Could not import EmbeddingService: {str(e)}. Using mock service.")
            from .mock_embedding_service import MockEmbeddingService
            return MockEmbeddingService(vector_store)

    @classmethod
    def _create_vector_search_with_retry(cls, service_class, vector_store: VectorStore, max_retries: int = 3):
        """
        Create a vector search service with retry capability.

        Args:
            service_class: The service class to instantiate
            vector_store: The vector store configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with retry capability
        """
        # Create the base service instance
        service = service_class(vector_store)

        # Create a wrapper class with retry capability
        class VectorSearchWithRetry:
            """Wrapper class that adds retry capability to service methods."""

            def __init__(self, service, vector_store):
                self.service = service
                self.vector_store = vector_store
                self.service_name = service.__class__.__name__

            @retry_with_exponential_backoff(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            def search(self, query, limit=10, case_id=None):
                """Search with retry capability."""
                return self.service.search(query, limit, case_id)

        return VectorSearchWithRetry(service, vector_store)

    @classmethod
    def _create_vector_search_with_fallback(cls, vector_store: VectorStore, max_retries: int = 3):
        """
        Create a vector search service with fallback to mock service.

        Args:
            vector_store: The vector store configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with fallback capability
        """
        from .vector_search import VectorSearchService
        from .mock_vector_search import MockVectorSearchService

        # Create the real service with retry capability
        real_service = cls._create_vector_search_with_retry(VectorSearchService, vector_store, max_retries)
        mock_service = MockVectorSearchService(vector_store)

        class VectorSearchWithFallback:
            """Wrapper class that tries real service first, then falls back to mock."""

            def __init__(self, real_service, mock_service, vector_store):
                self.real_service = real_service
                self.mock_service = mock_service
                self.vector_store = vector_store
                self.service_name = "VectorSearchService"

            def search(self, query, limit=10, case_id=None):
                """Search with fallback to mock service if real service fails."""
                start_time = time.time()

                try:
                    logger.info(f"Attempting to use real vector search service")
                    results = self.real_service.search(query, limit, case_id)

                    # Record successful service call
                    end_time = time.time()
                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=True,
                        response_time=end_time - start_time
                    )

                    return results

                except Exception as e:
                    # Record failed service call
                    end_time = time.time()
                    error_type = type(e).__name__
                    error_message = str(e)

                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=False,
                        response_time=end_time - start_time,
                        error_type=error_type,
                        error_message=error_message
                    )

                    logger.warning(f"Error using real vector search service: {error_message}. Falling back to mock service.")

                    # Use mock service as fallback
                    return self.mock_service.search(query, limit, case_id)

        return VectorSearchWithFallback(real_service, mock_service, vector_store)

    @classmethod
    def _create_embedding_service_with_retry(cls, service_class, vector_store: VectorStore, max_retries: int = 3):
        """
        Create an embedding service with retry capability.

        Args:
            service_class: The service class to instantiate
            vector_store: The vector store configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with retry capability
        """
        # Create the base service instance
        service = service_class(vector_store)

        # Create a wrapper class with retry capability
        class EmbeddingServiceWithRetry:
            """Wrapper class that adds retry capability to service methods."""

            def __init__(self, service, vector_store):
                self.service = service
                self.vector_store = vector_store
                self.dimensions = vector_store.dimensions
                self.embedding_model = vector_store.embedding_model
                self.service_name = service.__class__.__name__

            @retry_with_exponential_backoff(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            def get_embedding(self, text):
                """Get embedding with retry capability."""
                return self.service.get_embedding(text)

            @retry_with_exponential_backoff(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            def create_document_embedding(self, document):
                """Create document embedding with retry capability."""
                return self.service.create_document_embedding(document)

        return EmbeddingServiceWithRetry(service, vector_store)

    @classmethod
    def _create_embedding_service_with_fallback(cls, vector_store: VectorStore, max_retries: int = 3):
        """
        Create an embedding service with fallback to mock service.

        Args:
            vector_store: The vector store configuration
            max_retries: Maximum number of retries for service calls

        Returns:
            A service instance with fallback capability
        """
        from .embedding_service import EmbeddingService
        from .mock_embedding_service import MockEmbeddingService

        # Create the real service with retry capability
        real_service = cls._create_embedding_service_with_retry(EmbeddingService, vector_store, max_retries)
        mock_service = MockEmbeddingService(vector_store)

        class EmbeddingServiceWithFallback:
            """Wrapper class that tries real service first, then falls back to mock."""

            def __init__(self, real_service, mock_service, vector_store):
                self.real_service = real_service
                self.mock_service = mock_service
                self.vector_store = vector_store
                self.dimensions = vector_store.dimensions
                self.embedding_model = vector_store.embedding_model
                self.service_name = "EmbeddingService"

            def get_embedding(self, text):
                """Get embedding with fallback to mock service if real service fails."""
                start_time = time.time()

                try:
                    logger.info(f"Attempting to use real embedding service")
                    embedding = self.real_service.get_embedding(text)

                    # Record successful service call
                    end_time = time.time()
                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=True,
                        response_time=end_time - start_time
                    )

                    return embedding

                except Exception as e:
                    # Record failed service call
                    end_time = time.time()
                    error_type = type(e).__name__
                    error_message = str(e)

                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=False,
                        response_time=end_time - start_time,
                        error_type=error_type,
                        error_message=error_message
                    )

                    logger.warning(f"Error using real embedding service: {error_message}. Falling back to mock service.")
                    return self.mock_service.get_embedding(text)

            def create_document_embedding(self, document):
                """Create document embedding with fallback to mock service if real service fails."""
                start_time = time.time()

                try:
                    logger.info(f"Attempting to create real document embedding for document {document.id}")
                    embedding = self.real_service.create_document_embedding(document)

                    # Record successful service call
                    end_time = time.time()
                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=embedding is not None,
                        response_time=end_time - start_time,
                        error_type=None if embedding is not None else "EMBEDDING_FAILED",
                        error_message=None if embedding is not None else "Failed to create embedding"
                    )

                    if embedding:
                        return embedding

                    logger.warning(f"Real embedding service failed to create embedding. Falling back to mock service.")
                    return self.mock_service.create_document_embedding(document)

                except Exception as e:
                    # Record failed service call
                    end_time = time.time()
                    error_type = type(e).__name__
                    error_message = str(e)

                    ServiceMonitor.record_service_call(
                        service_name=self.service_name,
                        endpoint=self.vector_store.connection_string,
                        success=False,
                        response_time=end_time - start_time,
                        error_type=error_type,
                        error_message=error_message
                    )

                    logger.warning(f"Error creating real document embedding: {error_message}. Falling back to mock service.")
                    return self.mock_service.create_document_embedding(document)

        return EmbeddingServiceWithFallback(real_service, mock_service, vector_store)
