"""
Vector search service for semantic search.

This module provides services for semantic search using vector databases.
"""

import numpy as np
import logging
import ast
from typing import List, Dict, Any, Optional, Union
from django.db import connection
from ..models import VectorStore, DocumentEmbedding
from .embedding_service import EmbeddingService
from .. import settings as ai_settings

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
        logger.info(f"Initialized VectorSearchService with store: {vector_store.name}")

    def search(self,
               query: str,
               limit: int = None,
               threshold: float = None,
               case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: from settings)
            threshold: Minimum similarity threshold (default: from settings)
            case_id: Optional case ID to filter results

        Returns:
            List of documents with similarity scores
        """
        # Use default values from settings if not provided
        if limit is None:
            limit = ai_settings.VECTOR_SEARCH_TOP_K
        if threshold is None:
            threshold = ai_settings.VECTOR_SEARCH_THRESHOLD

        logger.info(f"Searching for: '{query}' (limit={limit}, threshold={threshold})")

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
                    WHERE 1 - (dv.embedding <=> %s) >= %s
                    """

                    params = [query_embedding.tolist(), query_embedding.tolist(), threshold]

                    if case_id:
                        sql += " AND d.case_id = %s"
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

                    logger.info(f"Found {len(documents)} documents with pgvector")
                    return documents
            except Exception as e:
                logger.error(f"Error searching with pgvector: {str(e)}")
                # Fall back to basic search using DocumentEmbedding model
                return self._fallback_search(query, limit, threshold, case_id)
        elif self.vector_store.store_type == 'chroma':
            try:
                from chromadb import Client, Settings

                # Parse connection string
                connection_parts = self.vector_store.connection_string.split('://')
                if len(connection_parts) > 1:
                    protocol, rest = connection_parts
                    host, port = rest.split(':')

                    client = Client(Settings(
                        chroma_api_impl="rest",
                        chroma_server_host=host,
                        chroma_server_http_port=port
                    ))
                else:
                    # Local persistent client
                    client = Client(Settings(
                        persist_directory=self.vector_store.connection_string or "./chroma_db"
                    ))

                # Get collection
                collection = client.get_collection(name="legal_documents")

                # Prepare filter if case_id is provided
                where_filter = None
                if case_id:
                    where_filter = {"case_id": str(case_id)}

                # Query the collection
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=limit,
                    where=where_filter
                )

                documents = []
                if results and 'ids' in results and len(results['ids']) > 0:
                    ids = results['ids'][0]
                    distances = results['distances'][0]
                    metadatas = results['metadatas'][0] if 'metadatas' in results else [{}] * len(ids)

                    for i, doc_id in enumerate(ids):
                        # Convert distance to similarity (ChromaDB returns distances, not similarities)
                        similarity = 1.0 - distances[i]

                        # Skip if below threshold
                        if similarity < threshold:
                            continue

                        metadata = metadatas[i] if i < len(metadatas) else {}

                        documents.append({
                            "id": int(doc_id),
                            "title": metadata.get('title', f"Document {doc_id}"),
                            "document_type": metadata.get('document_type', 'Unknown'),
                            "similarity": float(similarity)
                        })

                logger.info(f"Found {len(documents)} documents with ChromaDB")
                return documents
            except Exception as e:
                logger.error(f"Error searching with ChromaDB: {str(e)}")
                return self._fallback_search(query, limit, threshold, case_id)
        else:
            # Fall back to basic search using DocumentEmbedding model
            return self._fallback_search(query, limit, threshold, case_id)

    def _fallback_search(self, query: str, limit: int, threshold: float, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fallback search method when vector database is not available.
        Uses the DocumentEmbedding model directly or falls back to keyword search.

        Args:
            query: Search query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            case_id: Optional case ID to filter results

        Returns:
            List of documents with similarity scores
        """
        logger.info("Using fallback search method")
        try:
            # First try using DocumentEmbedding model if available
            try:
                # Get query embedding
                query_embedding = self.embedding_service.get_embedding(query)

                # Get all document embeddings
                embeddings_query = DocumentEmbedding.objects.select_related('document')

                # Filter by case if specified
                if case_id:
                    embeddings_query = embeddings_query.filter(document__case_id=case_id)

                embeddings = list(embeddings_query)

                if not embeddings:
                    logger.info("No document embeddings found, falling back to keyword search")
                    return self._keyword_search(query, limit, case_id)

                # Calculate similarity scores
                documents = []
                for doc_embedding in embeddings:
                    try:
                        # Get the embedding vector
                        if hasattr(doc_embedding, 'embedding_data'):
                            # If stored as string
                            doc_vector = np.array(ast.literal_eval(doc_embedding.embedding_data))
                        elif hasattr(doc_embedding, 'vector_id'):
                            # If using external vector store
                            # This is a placeholder - in a real implementation, you would
                            # retrieve the vector from the external store
                            continue
                        else:
                            logger.warning(f"No embedding data found for document {doc_embedding.document.id}")
                            continue

                        # Calculate cosine similarity
                        similarity = np.dot(query_embedding, doc_vector) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_vector))

                        # Skip if below threshold
                        if similarity < threshold:
                            continue

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
                logger.warning(f"Error in embedding-based fallback search: {str(e)}")
                return self._keyword_search(query, limit, case_id)

        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
            return []

    def _keyword_search(self, query: str, limit: int, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Simple keyword search as a last resort fallback.

        Args:
            query: Search query
            limit: Maximum number of results
            case_id: Optional case ID to filter results

        Returns:
            List of documents with mock similarity scores
        """
        logger.info(f"Using keyword search for query: '{query}'")

        try:
            from documents.models import Document

            # Simple keyword search
            queryset = Document.objects.filter(title__icontains=query)

            if case_id:
                queryset = queryset.filter(case_id=case_id)

            queryset = queryset.order_by('-uploaded_at')[:limit]

            documents = []
            for doc in queryset:
                documents.append({
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.get_document_type_display() if hasattr(doc, 'get_document_type_display') else doc.document_type,
                    "similarity": 0.8  # Mock similarity score
                })

            logger.info(f"Found {len(documents)} documents with keyword search")
            return documents
        except Exception as e:
            logger.error(f"Error with keyword search: {str(e)}")
            return []

    def similar_documents(self,
                         document_id: int,
                         limit: int = None,
                         threshold: float = None) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of the document to find similar documents for
            limit: Maximum number of results (default: from settings)
            threshold: Minimum similarity threshold (default: from settings)

        Returns:
            List of similar documents with similarity scores
        """
        # Use default values from settings if not provided
        if limit is None:
            limit = ai_settings.VECTOR_SEARCH_TOP_K
        if threshold is None:
            threshold = ai_settings.VECTOR_SEARCH_THRESHOLD

        logger.info(f"Finding documents similar to document ID: {document_id}")

        try:
            from documents.models import Document
            document = Document.objects.get(id=document_id)

            # Get document embedding or create if it doesn't exist
            try:
                doc_embedding = DocumentEmbedding.objects.get(document=document)
            except DocumentEmbedding.DoesNotExist:
                # Create embedding if it doesn't exist
                if not self.embedding_service:
                    from .embedding_service import EmbeddingService
                    self.embedding_service = EmbeddingService(self.vector_store)

                success = self.embedding_service.create_document_embedding(document)
                if not success:
                    logger.warning(f"Failed to create embedding for document {document_id}")
                    return []

                # Try to get the embedding again
                try:
                    doc_embedding = DocumentEmbedding.objects.get(document=document)
                except DocumentEmbedding.DoesNotExist:
                    logger.warning(f"Embedding still not found for document {document_id} after creation attempt")
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
                        WHERE d.id != %s AND 1 - (dv.embedding <=> (SELECT embedding FROM document_vectors WHERE document_id = %s)) >= %s
                        """

                        # Add case filter if document has a case
                        if document.case_id:
                            sql += " AND d.case_id = %s"
                            params = [document_id, document_id, document_id, threshold, document.case_id]
                        else:
                            params = [document_id, document_id, document_id, threshold]

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

                        logger.info(f"Found {len(documents)} similar documents with pgvector")
                        return documents
                except Exception as e:
                    logger.error(f"Error finding similar documents with pgvector: {str(e)}")
                    # Fall back to basic similarity calculation
                    return self._fallback_similar_documents(document, limit, threshold)
            elif self.vector_store.store_type == 'chroma':
                try:
                    from chromadb import Client, Settings

                    # Parse connection string
                    connection_parts = self.vector_store.connection_string.split('://')
                    if len(connection_parts) > 1:
                        protocol, rest = connection_parts
                        host, port = rest.split(':')

                        client = Client(Settings(
                            chroma_api_impl="rest",
                            chroma_server_host=host,
                            chroma_server_http_port=port
                        ))
                    else:
                        # Local persistent client
                        client = Client(Settings(
                            persist_directory=self.vector_store.connection_string or "./chroma_db"
                        ))

                    # Get collection
                    collection = client.get_collection(name="legal_documents")

                    # Prepare filter
                    where_filter = None
                    if document.case_id:
                        where_filter = {"case_id": str(document.case_id)}

                    # Get the document's embedding
                    doc_result = collection.get(ids=[str(document_id)], include=["embeddings"])

                    if not doc_result or not doc_result["embeddings"]:
                        logger.warning(f"No embedding found in ChromaDB for document {document_id}")
                        return []

                    # Query the collection for similar documents
                    results = collection.query(
                        query_embeddings=doc_result["embeddings"],
                        n_results=limit + 1,  # +1 because the document itself will be included
                        where=where_filter
                    )

                    documents = []
                    if results and 'ids' in results and len(results['ids']) > 0:
                        ids = results['ids'][0]
                        distances = results['distances'][0]
                        metadatas = results['metadatas'][0] if 'metadatas' in results else [{}] * len(ids)

                        for i, doc_id in enumerate(ids):
                            # Skip the document itself
                            if doc_id == str(document_id):
                                continue

                            # Convert distance to similarity
                            similarity = 1.0 - distances[i]

                            # Skip if below threshold
                            if similarity < threshold:
                                continue

                            metadata = metadatas[i] if i < len(metadatas) else {}

                            documents.append({
                                "id": int(doc_id),
                                "title": metadata.get('title', f"Document {doc_id}"),
                                "document_type": metadata.get('document_type', 'Unknown'),
                                "similarity": float(similarity)
                            })

                    logger.info(f"Found {len(documents)} similar documents with ChromaDB")
                    return documents
                except Exception as e:
                    logger.error(f"Error finding similar documents with ChromaDB: {str(e)}")
                    return self._fallback_similar_documents(document, limit, threshold)
            else:
                # Fall back to basic similarity calculation
                return self._fallback_similar_documents(document, limit, threshold)

        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []

    def _fallback_similar_documents(self, document, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """
        Fallback method to find similar documents when vector database is not available.

        Args:
            document: Document to find similar documents for
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of similar documents with similarity scores
        """
        logger.info(f"Using fallback method to find documents similar to {document.id}")
        try:
            # Get document embedding
            try:
                doc_embedding = DocumentEmbedding.objects.get(document=document)
                if hasattr(doc_embedding, 'embedding_data'):
                    source_vector = np.array(ast.literal_eval(doc_embedding.embedding_data))
                else:
                    # If using external vector store with no local embedding data
                    logger.warning(f"No embedding data available for document {document.id}")
                    return self._keyword_similar_documents(document, limit)
            except (DocumentEmbedding.DoesNotExist, Exception) as e:
                logger.warning(f"Could not get embedding for document {document.id}: {str(e)}")
                # If no embedding exists, create one
                if not self.embedding_service:
                    from .embedding_service import EmbeddingService
                    self.embedding_service = EmbeddingService(self.vector_store)

                # Get document text
                from documents.utils import extract_text_from_document
                text = extract_text_from_document(document)
                if not text:
                    logger.warning(f"Could not extract text from document {document.id}")
                    return self._keyword_similar_documents(document, limit)

                # Create embedding
                source_vector = self.embedding_service.get_embedding(text)

            # Get all other document embeddings
            other_embeddings = DocumentEmbedding.objects.exclude(document=document).select_related('document')

            # Filter by same case if document has a case
            if hasattr(document, 'case') and document.case:
                other_embeddings = other_embeddings.filter(document__case=document.case)

            # Calculate similarity scores
            documents = []
            for other_embedding in other_embeddings:
                try:
                    # Get the embedding vector
                    if hasattr(other_embedding, 'embedding_data'):
                        # If stored as string
                        other_vector = np.array(ast.literal_eval(other_embedding.embedding_data))
                    else:
                        # Skip if no embedding data available
                        continue

                    # Calculate cosine similarity
                    similarity = np.dot(source_vector, other_vector) / (np.linalg.norm(source_vector) * np.linalg.norm(other_vector))

                    # Skip if below threshold
                    if similarity < threshold:
                        continue

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
            return self._keyword_similar_documents(document, limit)

    def _keyword_similar_documents(self, document, limit: int) -> List[Dict[str, Any]]:
        """
        Find similar documents using keyword matching as a last resort.

        Args:
            document: Document to find similar documents for
            limit: Maximum number of results

        Returns:
            List of documents with mock similarity scores
        """
        logger.info(f"Using keyword matching to find documents similar to {document.id}")

        try:
            from documents.models import Document

            # Get words from document title
            words = document.title.split()
            if len(words) <= 1:
                # If title has only one word, use it
                queryset = Document.objects.filter(title__icontains=document.title)
            else:
                # Use the most significant words from the title
                significant_words = [w for w in words if len(w) > 3][:3]  # Up to 3 words with length > 3
                if not significant_words:
                    significant_words = words[:2]  # Fallback to first 2 words

                # Build query
                from django.db.models import Q
                query = Q()
                for word in significant_words:
                    query |= Q(title__icontains=word)

                queryset = Document.objects.filter(query)

            # Exclude the current document
            queryset = queryset.exclude(id=document.id)

            # Filter by same case if document has a case
            if hasattr(document, 'case') and document.case:
                queryset = queryset.filter(case=document.case)

            queryset = queryset.order_by('-uploaded_at')[:limit]

            documents = []
            for doc in queryset:
                documents.append({
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.get_document_type_display() if hasattr(doc, 'get_document_type_display') else doc.document_type,
                    "similarity": 0.7  # Mock similarity score
                })

            logger.info(f"Found {len(documents)} similar documents with keyword matching")
            return documents
        except Exception as e:
            logger.error(f"Error with keyword similar documents: {str(e)}")
            return []
