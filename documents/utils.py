"""
Utility functions for document handling.
"""

import os
import logging
import tempfile
from typing import Optional
from django.conf import settings
from .models import Document

logger = logging.getLogger(__name__)

def extract_text_from_document(document: Document) -> Optional[str]:
    """
    Extract text content from a document file.
    
    Args:
        document: The Document model instance
        
    Returns:
        Extracted text or None if extraction failed
    """
    if not document.file:
        logger.warning(f"Document {document.id} has no file")
        return None
        
    file_path = document.file.path
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # Plain text files
        if file_extension in ['.txt', '.md', '.csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        # PDF files
        elif file_extension == '.pdf':
            try:
                import PyPDF2
                
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page_num in range(len(pdf_reader.pages)):
                        text += pdf_reader.pages[page_num].extract_text() + "\n"
                    return text
            except ImportError:
                logger.warning("PyPDF2 not installed, falling back to basic text extraction")
                # Fall back to basic text extraction
                with open(file_path, 'rb') as f:
                    return str(f.read())
                    
        # Word documents
        elif file_extension in ['.doc', '.docx']:
            try:
                import docx
                
                doc = docx.Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            except ImportError:
                logger.warning("python-docx not installed, falling back to basic text extraction")
                # Fall back to basic text extraction
                with open(file_path, 'rb') as f:
                    return str(f.read())
        
        # Other file types - just read as binary and convert to string
        else:
            with open(file_path, 'rb') as f:
                return str(f.read())
                
    except Exception as e:
        logger.error(f"Error extracting text from document {document.id}: {str(e)}")
        return None
        
def get_document_preview(document: Document, max_length: int = 1000) -> Optional[str]:
    """
    Get a preview of the document content.
    
    Args:
        document: The Document model instance
        max_length: Maximum length of the preview
        
    Returns:
        Document preview or None if extraction failed
    """
    text = extract_text_from_document(document)
    if text:
        # Truncate to max_length
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    return None
