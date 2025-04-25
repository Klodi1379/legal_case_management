import numpy as np
import logging
import ast
from typing import List, Dict, Any, Optional
from django.db import connection
from ..models import Document, VectorStore, DocumentEmbedding

logger = logging.getLogger(__name__)

class VectorSearchService:
    """Service for semantic search using vector database."""

    def __init__(self, vector_store: VectorStore, embedding_service=None):
        """
        Initialize with a vector store from the database.

        Args:
            vector_store: Vector store configuration
            embedding_service: Optional embedding service for query embedding
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def search(self,
               query: str,
               limit: int = 10,
               case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query
            limit: Maximum number of results
            case_id: Optional case ID to filter results

        Returns:
            List of documents with similarity scores
        """
        # Get query embedding
        if not self.embedding_service:
            from .embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService(self.vector_store)

        query_embedding = self.embedding_service.get_embedding(query)

        # Perform search based on vector store type
        if self.vector_store.store_type == 'pgvector':
            try:
                # Using Django ORM with pgvector extension
                with connection.cursor() as cursor:
                    sql = """
                    SELECT d.id, d.title, d.document_type,
                           1 - (dv.embedding <=> %s) AS similarity
                    FROM documents_document d
                    JOIN document_vectors dv ON d.id = dv.document_id
                    """

                    params = [query_embedding.tolist()]

                    if case_id:
                        sql += " WHERE d.case_id = %s"
                        params.append(case_id)

                    sql += " ORDER BY similarity DESC LIMIT %s"
                    params.append(limit)

                    cursor.execute(sql, params)
                    results = cursor.fetchall()

                    documents = []
                    for row in results:
                        doc_id, title, doc_type, similarity = row
                        documents.append({
                            "id": doc_id,
                            "title": title,
                            "document_type": doc_type,
                            "similarity": float(similarity)
                        })

                    return documents
            except Exception as e:
                logger.error(f"Error performing vector search with pgvector: {str(e)}")
                # Fall back to basic search using DocumentEmbedding model
                return self._fallback_search(query, limit, case_id)
        else:
            # Fall back to basic search using DocumentEmbedding model
            return self._fallback_search(query, limit, case_id)
            
    def _fallback_search(self, query: str, limit: int, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fallback search method when pgvector is not available.
        Uses the DocumentEmbedding model directly.
        """
        logger.info("Using fallback search method with DocumentEmbedding model")
        try:
            # Get query embedding
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Get all document embeddings
            embeddings_query = DocumentEmbedding.objects.select_related('document')
            
            # Filter by case if specified
            if case_id:
                embeddings_query = embeddings_query.filter(document__case_id=case_id)
                
            embeddings = list(embeddings_query)
            
            # Calculate similarity scores
            documents = []
            for doc_embedding in embeddings:
                try:
                    # Parse the embedding data from string
                    doc_vector = np.array(ast.literal_eval(doc_embedding.embedding_data))
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, doc_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_vector))
                    
                    documents.append({
                        "id": doc_embedding.document.id,
                        "title": doc_embedding.document.title,
                        "document_type": doc_embedding.document.document_type,
                        "similarity": float(similarity)
                    })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for document {doc_embedding.document.id}: {str(e)}")
                    continue
            
            # Sort by similarity score
            documents.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Limit results
            return documents[:limit]
            
        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
            return []

    def similar_documents(self, document_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of the document to find similar documents for
            limit: Maximum number of results

        Returns:
            List of similar documents with similarity scores
        """
        try:
            document = Document.objects.get(id=document_id)

            # Get document embedding
            try:
                doc_embedding = DocumentEmbedding.objects.get(document=document)
            except DocumentEmbedding.DoesNotExist:
                # Create embedding if it doesn't exist
                if not self.embedding_service:
                    from .embedding_service import EmbeddingService
                    self.embedding_service = EmbeddingService(self.vector_store)

                doc_embedding = self.embedding_service.create_document_embedding(document)
                if not doc_embedding:
                    return []

            # Perform search based on vector store type
            if self.vector_store.store_type == 'pgvector':
                try:
                    with connection.cursor() as cursor:
                        sql = """
                        SELECT d.id, d.title, d.document_type, 
                               1 - (dv.embedding <=> (SELECT embedding FROM document_vectors WHERE document_id = %s)) AS similarity
                        FROM documents_document d
                        JOIN document_vectors dv ON d.id = dv.document_id
                        WHERE d.id != %s
                        ORDER BY similarity DESC
                        LIMIT %s
                        """

                        cursor.execute(sql, [document_id, document_id, limit])
                        results = cursor.fetchall()

                        documents = []
                        for row in results:
                            doc_id, title, doc_type, similarity = row
                            documents.append({
                                "id": doc_id,
                                "title": title,
                                "document_type": doc_type,
                                "similarity": float(similarity)
                            })

                        return documents
                except Exception as e:
                    logger.error(f"Error finding similar documents with pgvector: {str(e)}")
                    # Fall back to basic similarity calculation
                    return self._fallback_similar_documents(document, limit)
            else:
                # Fall back to basic similarity calculation
                return self._fallback_similar_documents(document, limit)
        
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
                
    def _fallback_similar_documents(self, document: Document, limit: int) -> List[Dict[str, Any]]:
        """
        Fallback method to find similar documents when pgvector is not available.
        """
        logger.info(f"Using fallback method to find documents similar to {document.id}")
        try:
            # Get document embedding
            try:
                doc_embedding = DocumentEmbedding.objects.get(document=document)
                source_vector = np.array(ast.literal_eval(doc_embedding.embedding_data))
            except (DocumentEmbedding.DoesNotExist, Exception) as e:
                logger.warning(f"Could not get embedding for document {document.id}: {str(e)}")
                # If no embedding exists, create one
                if not self.embedding_service:
                    from .embedding_service import EmbeddingService
                    self.embedding_service = EmbeddingService(self.vector_store)
                
                # Get document text
                text = document.file.read().decode('utf-8', errors='ignore') if document.file else document.title
                if document.file:
                    document.file.seek(0)
                
                # Create embedding
                source_vector = self.embedding_service.get_embedding(text)
            
            # Get all other document embeddings
            other_embeddings = DocumentEmbedding.objects.exclude(document=document).select_related('document')
            
            # Filter by same case if document has a case
            if document.case:
                other_embeddings = other_embeddings.filter(document__case=document.case)
            
            # Calculate similarity scores
            documents = []
            for other_embedding in other_embeddings:
                try:
                    # Parse the embedding data from string
                    other_vector = np.array(ast.literal_eval(other_embedding.embedding_data))
                    
                    # Calculate cosine similarity
                    similarity = np.dot(source_vector, other_vector) / (np.linalg.norm(source_vector) * np.linalg.norm(other_vector))
                    
                    documents.append({
                        "id": other_embedding.document.id,
                        "title": other_embedding.document.title,
                        "document_type": other_embedding.document.document_type,
                        "similarity": float(similarity)
                    })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for document {other_embedding.document.id}: {str(e)}")
                    continue
            
            # Sort by similarity score
            documents.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Limit results
            return documents[:limit]
            
        except Exception as e:
            logger.error(f"Error in fallback similar documents: {str(e)}")
            return []
