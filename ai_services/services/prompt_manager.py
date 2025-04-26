"""
Prompt manager for legal-specific prompts.

This module provides services for building and managing prompts for
various legal tasks using LLMs.
"""

import logging
import string
import os
from typing import Dict, Any, Optional, Union
from django.conf import settings
from ..models import PromptTemplate
from documents.models import Document
from documents.utils import extract_text_from_document
from cases.models import Case

logger = logging.getLogger(__name__)

class PromptManager:
    """Manager for building and formatting prompts for legal tasks."""

    def format_prompt(self, template: Union[PromptTemplate, str], context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a prompt template with context variables.

        Args:
            template: PromptTemplate instance or string
            context: Dictionary of context variables

        Returns:
            Formatted prompt string
        """
        if context is None:
            context = {}

        try:
            # If template is a PromptTemplate instance, get the template string
            if hasattr(template, 'template_text'):
                template_str = template.template_text
            elif hasattr(template, 'prompt_template'):
                template_str = template.prompt_template
            else:
                template_str = str(template)

            # Format the template with the context
            formatter = string.Formatter()
            return formatter.format(template_str, **context)
        except KeyError as e:
            logger.warning(f"Missing context variable in prompt template: {str(e)}")
            # Return template with missing variables marked
            return template_str
        except Exception as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            return template_str

    def build_document_analysis_prompt(self,
                                      template: PromptTemplate,
                                      document: Document,
                                      custom_instructions: str = '') -> str:
        """
        Build a prompt for document analysis.

        Args:
            template: PromptTemplate instance
            document: Document instance
            custom_instructions: Custom instructions from the user

        Returns:
            Formatted prompt string
        """
        try:
            logger.info(f"Building document analysis prompt for document: {document.title}")

            # Get document content
            document_content = extract_text_from_document(document)
            if not document_content:
                document_content = f"[Unable to extract content from {document.title}]"

            # Build context
            context = {
                'document_title': document.title,
                'document_type': document.get_document_type_display() if hasattr(document, 'get_document_type_display') else document.document_type,
                'document_content': document_content,
                'custom_instructions': custom_instructions,
            }

            # Add case context if available
            if document.case:
                context.update({
                    'case_title': document.case.title,
                    'case_number': document.case.case_number,
                    'case_type': document.case.get_case_type_display() if hasattr(document.case, 'get_case_type_display') else document.case.case_type,
                    'case_status': document.case.get_status_display() if hasattr(document.case, 'get_status_display') else document.case.status,
                })

            # Format the prompt
            return self.format_prompt(template, context)
        except Exception as e:
            logger.error(f"Error building document analysis prompt: {str(e)}")
            return f"Please analyze this document: {document.title}\n\n{document_content}\n\n{custom_instructions}"

    def build_legal_research_prompt(self,
                                   template: PromptTemplate,
                                   research_question: str,
                                   case: Optional[Case] = None,
                                   context_documents: Optional[list] = None,
                                   custom_instructions: str = '') -> str:
        """
        Build a prompt for legal research.

        Args:
            template: PromptTemplate instance
            research_question: The research question
            case: Optional Case instance for context
            context_documents: Optional list of Document instances for context
            custom_instructions: Custom instructions from the user

        Returns:
            Formatted prompt string
        """
        try:
            logger.info(f"Building legal research prompt for question: {research_question}")

            # Build context
            context = {
                'research_question': research_question,
                'custom_instructions': custom_instructions,
            }

            # Add case context if available
            if case:
                context.update({
                    'case_title': case.title,
                    'case_number': case.case_number,
                    'case_type': case.get_case_type_display() if hasattr(case, 'get_case_type_display') else case.case_type,
                    'case_description': case.description,
                })

            # Add context documents if available
            if context_documents:
                documents_text = ""
                for i, doc in enumerate(context_documents, 1):
                    doc_content = extract_text_from_document(doc)
                    if doc_content:
                        documents_text += f"\nDocument {i}: {doc.title}\n{doc_content}\n"

                context['context_documents'] = documents_text

            # Format the prompt
            return self.format_prompt(template, context)
        except Exception as e:
            logger.error(f"Error building legal research prompt: {str(e)}")
            return f"Please research the following legal question: {research_question}\n\n{custom_instructions}"

    def build_document_generation_prompt(self,
                                        template: PromptTemplate,
                                        document_type: str,
                                        case: Optional[Case] = None,
                                        context_data: Optional[Dict[str, Any]] = None,
                                        custom_instructions: str = '') -> str:
        """
        Build a prompt for document generation.

        Args:
            template: PromptTemplate instance
            document_type: Type of document to generate
            case: Optional Case instance for context
            context_data: Optional dictionary of context data
            custom_instructions: Custom instructions from the user

        Returns:
            Formatted prompt string
        """
        try:
            logger.info(f"Building document generation prompt for type: {document_type}")

            # Build context
            context = {
                'document_type': document_type,
                'custom_instructions': custom_instructions,
            }

            # Add case context if available
            if case:
                context.update({
                    'case_title': case.title,
                    'case_number': case.case_number,
                    'case_type': case.get_case_type_display() if hasattr(case, 'get_case_type_display') else case.case_type,
                    'client_name': case.client.get_display_name() if hasattr(case.client, 'get_display_name') else case.client.company_name,
                })

                # Add opposing party if available
                if hasattr(case, 'opposing_counsel') and case.opposing_counsel:
                    context['opposing_counsel'] = case.opposing_counsel

            # Add additional context data if available
            if context_data:
                context.update(context_data)

            # Format the prompt
            return self.format_prompt(template, context)
        except Exception as e:
            logger.error(f"Error building document generation prompt: {str(e)}")
            return f"Please generate a {document_type} document.\n\n{custom_instructions}"
