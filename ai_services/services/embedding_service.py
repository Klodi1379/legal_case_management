"""
Embedding service for document vectorization.

This module provides services for creating and managing document embeddings
for semantic search capabilities.
"""

import numpy as np
import logging
import requests
import json
from typing import List, Dict, Any, Optional, Union
from django.conf import settings
from ..models import VectorStore, Document
from .. import settings as ai_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for creating and storing document embeddings."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize with a vector store from the database.
        
        Args:
            vector_store: The vector store configuration
        """
        self.vector_store = vector_store
        self.embedding_model = vector_store.embedding_model
        self.dimensions = vector_store.dimensions
        logger.info(f"Initialized EmbeddingService with store: {vector_store.name}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using the configured embedding model.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Numpy array containing the embedding vector
        """
        logger.info(f"Getting embedding with model: {self.embedding_model}")
        
        try:
            # Prepare the request
            endpoint_url = ai_settings.DEFAULT_EMBEDDING_ENDPOINT
            
            payload = {
                "model": self.embedding_model,
                "input": text,
            }
            
            headers = {"Content-Type": "application/json"}
            
            # Send request to the embedding API
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=headers,
                timeout=ai_settings.LLM_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"Embedding API response: {json.dumps(result, indent=2)}")
            
            # Extract embedding based on API response format
            if 'data' in result and len(result['data']) > 0:
                # OpenAI-like format
                embedding = result['data'][0]['embedding']
            elif 'embedding' in result:
                # Simple format
                embedding = result['embedding']
            else:
                raise ValueError(f"Unexpected embedding API response format: {result}")
                
            return np.array(embedding)
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Return zeros array as fallback
            return np.zeros(self.dimensions)
    
    def create_document_embedding(self, document: Document) -> bool:
        """
        Create and store embedding for a document.
        
        Args:
            document: Document to create embedding for
            
        Returns:
            True if successful, False otherwise
        """
        from documents.utils import extract_text_from_document
        
        try:
            logger.info(f"Creating embedding for document: {document.title}")
            
            # Get document text content
            text = extract_text_from_document(document)
            if not text:
                logger.warning(f"No text content extracted from document: {document.title}")
                return False
            
            # Get embedding
            embedding_vector = self.get_embedding(text)
            
            # Store in vector database based on the type
            if self.vector_store.store_type == 'pgvector':
                # Using Django ORM with pgvector extension
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO document_vectors (document_id, embedding) VALUES (%s, %s) RETURNING id",
                        [document.id, embedding_vector.tolist()]
                    )
                    vector_id = cursor.fetchone()[0]
                    logger.info(f"Stored embedding in pgvector with ID: {vector_id}")
            elif self.vector_store.store_type == 'chroma':
                # Using ChromaDB
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
                
                # Get or create collection
                collection = client.get_or_create_collection(
                    name="legal_documents",
                    embedding_function=None  # We're providing our own embeddings
                )
                
                # Add document to collection
                collection.add(
                    ids=[str(document.id)],
                    embeddings=[embedding_vector.tolist()],
                    metadatas=[{
                        "title": document.title,
                        "document_type": document.document_type,
                        "case_id": str(document.case.id) if document.case else None,
                    }],
                    documents=[text]
                )
                logger.info(f"Stored embedding in ChromaDB for document: {document.title}")
            else:
                # Mock or other vector store
                logger.info(f"Using mock vector store for document: {document.title}")
                # Just log that we would store it
                
            return True
            
        except Exception as e:
            logger.error(f"Error creating document embedding: {str(e)}")
            return False
    
    def update_document_embedding(self, document: Document) -> bool:
        """
        Update embedding for a document.
        
        Args:
            document: Document to update embedding for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating embedding for document: {document.title}")
            
            # Delete existing embedding
            if self.vector_store.store_type == 'pgvector':
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM document_vectors WHERE document_id = %s",
                        [document.id]
                    )
            elif self.vector_store.store_type == 'chroma':
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
                
                # Delete document from collection
                collection.delete(ids=[str(document.id)])
            
            # Create new embedding
            return self.create_document_embedding(document)
            
        except Exception as e:
            logger.error(f"Error updating document embedding: {str(e)}")
            return False
