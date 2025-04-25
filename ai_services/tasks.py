import logging
from celery import shared_task
from django.utils import timezone
from .models import AIAnalysisRequest, Document, VectorStore
# Use the service factory to get appropriate services
from .services.service_factory import AIServiceFactory

logger = logging.getLogger(__name__)

@shared_task
def process_analysis_request(request_id: int):
    """
    Process an AI analysis request asynchronously.

    Args:
        request_id: ID of the AIAnalysisRequest to process
    """
    logger.info(f"Processing analysis request {request_id}")
    
    try:
        # Get the analysis request
        analysis_request = AIAnalysisRequest.objects.get(id=request_id)
        model = analysis_request.llm_model
        
        # Get the appropriate service with fallback capability
        service_class = AIServiceFactory.get_llm_service(model)
        
        # Process the request
        return service_class.process_analysis_request(request_id)
    except Exception as e:
        logger.error(f"Error processing analysis request {request_id}: {str(e)}", exc_info=True)
        return False

@shared_task
def create_document_embeddings(document_id: int, vector_store_id: int):
    """
    Create embeddings for a document asynchronously.

    Args:
        document_id: ID of the Document to create embeddings for
        vector_store_id: ID of the VectorStore to use
    """
    logger.info(f"Creating embeddings for document {document_id}")

    try:
        document = Document.objects.get(id=document_id)
        vector_store = VectorStore.objects.get(id=vector_store_id)

        # Get the appropriate embedding service with fallback capability
        embedding_service = AIServiceFactory.get_embedding_service(vector_store)
        embedding = embedding_service.create_document_embedding(document)

        return embedding is not None

    except Exception as e:
        logger.error(f"Error creating document embeddings: {str(e)}", exc_info=True)
        return False

@shared_task
def batch_process_documents(case_id: int = None):
    """
    Process all unembedded documents in a case or the entire system.

    Args:
        case_id: Optional case ID to filter documents
    """
    logger.info(f"Batch processing documents for case {case_id if case_id else 'all'}")

    from .models import Document, VectorStore, DocumentEmbedding

    # Get documents without embeddings
    query = Document.objects.exclude(id__in=DocumentEmbedding.objects.values_list('document_id', flat=True))

    if case_id:
        query = query.filter(case_id=case_id)

    # Get default vector store
    vector_store = VectorStore.objects.filter(is_active=True).first()
    if not vector_store:
        logger.error("No active vector store configured")
        return {"error": "No active vector store configured"}

    # Process each document
    success_count = 0
    error_count = 0

    for document in query:
        try:
            create_document_embeddings.delay(document.id, vector_store.id)
            success_count += 1
        except Exception as e:
            logger.error(f"Error scheduling document {document.id}: {str(e)}")
            error_count += 1

    return {
        "scheduled": success_count,
        "errors": error_count,
        "total": success_count + error_count
    }
