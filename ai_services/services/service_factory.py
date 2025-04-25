import logging
from typing import Union, Optional
from django.conf import settings
from .. import settings as ai_settings
from ..models import LLMModel, VectorStore

logger = logging.getLogger(__name__)

class AIServiceFactory:
    """
    Factory class for creating AI service instances.
    
    This factory decides whether to use real or mock services based on configuration
    and availability of the real services.
    """
    
    @classmethod
    def get_llm_service(cls, model_instance: LLMModel, use_mock_fallback: bool = None):
        """
        Get an LLM service instance.
        
        Args:
            model_instance: The LLM model configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            
        Returns:
            An instance of GemmaService or MockGemmaService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES
        
        # Use settings value if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK
        
        if not ai_enabled:
            logger.info("AI features are disabled. Using mock service.")
            from .mock_llm_service import MockGemmaService
            return MockGemmaService(model_instance)
        
        # Try to import and use the real service
        try:
            from .llm_service import GemmaService
            
            # If mock fallback is enabled, use a wrapper that will try real service first
            if use_mock_fallback:
                return cls._create_llm_service_with_fallback(model_instance)
            
            # Otherwise, use the real service directly
            return GemmaService(model_instance)
            
        except ImportError as e:
            logger.warning(f"Could not import GemmaService: {str(e)}. Using mock service.")
            from .mock_llm_service import MockGemmaService
            return MockGemmaService(model_instance)
    
    @classmethod
    def _create_llm_service_with_fallback(cls, model_instance: LLMModel):
        """
        Create an LLM service with fallback to mock service.
        
        This creates a wrapper around the real service that will try the real service first,
        and if it fails, fall back to the mock service.
        
        Args:
            model_instance: The LLM model configuration
            
        Returns:
            A service instance with fallback capability
        """
        from .llm_service import GemmaService
        from .mock_llm_service import MockGemmaService
        
        class LLMServiceWithFallback:
            """Wrapper class that tries real service first, then falls back to mock."""
            
            def __init__(self, model):
                self.real_service = GemmaService(model)
                self.mock_service = MockGemmaService(model)
                self.model = model
            
            def generate_text(self, prompt, system_prompt=None, **kwargs):
                """Generate text with fallback to mock service if real service fails."""
                try:
                    logger.info(f"Attempting to use real LLM service with model {self.model.name}")
                    result = self.real_service.generate_text(prompt, system_prompt, **kwargs)
                    
                    # If there was an error, try the mock service
                    if result.get("error"):
                        logger.warning(f"Real LLM service returned error: {result['error']}. Falling back to mock service.")
                        return self.mock_service.generate_text(prompt, system_prompt, **kwargs)
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Error using real LLM service: {str(e)}. Falling back to mock service.")
                    return self.mock_service.generate_text(prompt, system_prompt, **kwargs)
            
            @classmethod
            def process_analysis_request(cls, request_id: int):
                """Process an analysis request with fallback capability."""
                try:
                    return GemmaService.process_analysis_request(request_id)
                except Exception as e:
                    logger.warning(f"Error processing analysis with real service: {str(e)}. Falling back to mock service.")
                    return MockGemmaService.process_analysis_request(request_id)
        
        return LLMServiceWithFallback(model_instance)
    
    @classmethod
    def get_vector_search_service(cls, vector_store: VectorStore, use_mock_fallback: bool = None):
        """
        Get a vector search service instance.
        
        Args:
            vector_store: The vector store configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            
        Returns:
            An instance of VectorSearchService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES
        
        # Use settings value if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK
        
        if not ai_enabled:
            logger.info("AI features are disabled. Using mock vector search service.")
            from .mock_vector_search import MockVectorSearchService
            return MockVectorSearchService(vector_store)
        
        # Try to import and use the real service
        try:
            from .vector_search import VectorSearchService
            return VectorSearchService(vector_store)
        except ImportError as e:
            logger.warning(f"Could not import VectorSearchService: {str(e)}. Using mock service.")
            from .mock_vector_search import MockVectorSearchService
            return MockVectorSearchService(vector_store)
    
    @classmethod
    def get_embedding_service(cls, vector_store: VectorStore, use_mock_fallback: bool = None):
        """
        Get an embedding service instance.
        
        Args:
            vector_store: The vector store configuration
            use_mock_fallback: Whether to use mock service as fallback if real service fails
            
        Returns:
            An instance of EmbeddingService
        """
        # Check if AI features are enabled
        ai_enabled = ai_settings.ENABLE_AI_FEATURES
        
        # Use settings value if not explicitly provided
        if use_mock_fallback is None:
            use_mock_fallback = ai_settings.USE_MOCK_FALLBACK
        
        if not ai_enabled:
            logger.info("AI features are disabled. Using mock embedding service.")
            from .mock_embedding_service import MockEmbeddingService
            return MockEmbeddingService(vector_store)
        
        # Try to import and use the real service
        try:
            from .embedding_service import EmbeddingService
            
            # If mock fallback is enabled, use a wrapper that will try real service first
            if use_mock_fallback:
                return cls._create_embedding_service_with_fallback(vector_store)
            
            # Otherwise, use the real service directly
            return EmbeddingService(vector_store)
            
        except ImportError as e:
            logger.warning(f"Could not import EmbeddingService: {str(e)}. Using mock service.")
            from .mock_embedding_service import MockEmbeddingService
            return MockEmbeddingService(vector_store)
    
    @classmethod
    def _create_embedding_service_with_fallback(cls, vector_store: VectorStore):
        """
        Create an embedding service with fallback to mock service.
        
        Args:
            vector_store: The vector store configuration
            
        Returns:
            A service instance with fallback capability
        """
        from .embedding_service import EmbeddingService
        from .mock_embedding_service import MockEmbeddingService
        
        class EmbeddingServiceWithFallback:
            """Wrapper class that tries real service first, then falls back to mock."""
            
            def __init__(self, vector_store):
                self.real_service = EmbeddingService(vector_store)
                self.mock_service = MockEmbeddingService(vector_store)
                self.vector_store = vector_store
                self.dimensions = vector_store.dimensions
                self.embedding_model = vector_store.embedding_model
            
            def get_embedding(self, text):
                """Get embedding with fallback to mock service if real service fails."""
                try:
                    logger.info(f"Attempting to use real embedding service")
                    embedding = self.real_service.get_embedding(text)
                    return embedding
                except Exception as e:
                    logger.warning(f"Error using real embedding service: {str(e)}. Falling back to mock service.")
                    return self.mock_service.get_embedding(text)
            
            def create_document_embedding(self, document):
                """Create document embedding with fallback to mock service if real service fails."""
                try:
                    logger.info(f"Attempting to create real document embedding for document {document.id}")
                    embedding = self.real_service.create_document_embedding(document)
                    if embedding:
                        return embedding
                    
                    logger.warning(f"Real embedding service failed to create embedding. Falling back to mock service.")
                    return self.mock_service.create_document_embedding(document)
                except Exception as e:
                    logger.warning(f"Error creating real document embedding: {str(e)}. Falling back to mock service.")
                    return self.mock_service.create_document_embedding(document)
        
        return EmbeddingServiceWithFallback(vector_store)
