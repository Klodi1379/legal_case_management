import logging
from typing import List, Dict, Any, Optional
from ..models import Document

logger = logging.getLogger(__name__)

class MockVectorSearchService:
    """Mock service for semantic search."""

    def __init__(self, vector_store=None, embedding_service=None):
        """Initialize the mock service."""
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def search(self,
               query: str,
               limit: int = 10,
               case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Mock search for documents similar to the query.

        Args:
            query: Search query
            limit: Maximum number of results
            case_id: Optional case ID to filter results

        Returns:
            List of documents with similarity scores
        """
        logger.info(f"Mock search for: {query}")
        
        # Get some documents to return as mock results
        document_query = Document.objects.all()
        if case_id:
            document_query = document_query.filter(case_id=case_id)
        
        documents = []
        for i, doc in enumerate(document_query[:limit]):
            # Mock similarity score decreasing with each result
            similarity = 0.95 - (i * 0.05)
            documents.append({
                "id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "similarity": similarity
            })
        
        return documents

    def similar_documents(self, document_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Mock finding documents similar to a given document.

        Args:
            document_id: ID of the document to find similar documents for
            limit: Maximum number of results

        Returns:
            List of similar documents with similarity scores
        """
        logger.info(f"Mock finding documents similar to: {document_id}")
        
        try:
            # Get the source document
            source_document = Document.objects.get(id=document_id)
            
            # Get other documents (preferably from the same case)
            document_query = Document.objects.exclude(id=document_id)
            
            if source_document.case:
                # Prioritize documents from the same case
                documents_same_case = list(document_query.filter(case=source_document.case)[:limit])
                documents_other_cases = list(document_query.exclude(case=source_document.case)[:max(0, limit - len(documents_same_case))])
                documents = documents_same_case + documents_other_cases
            else:
                documents = list(document_query[:limit])
            
            # Create mock results
            results = []
            for i, doc in enumerate(documents[:limit]):
                # Mock similarity score decreasing with each result
                similarity = 0.9 - (i * 0.1)
                results.append({
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "similarity": similarity
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
