# Legal Case Management System

A comprehensive legal case management system built with Django and LLM integration.

## Features

- **Case Management**: Track case details, status, and associated parties
- **Document Management**: Store, organize, and analyze legal documents
- **Client Management**: Manage client information and communications
- **AI Integration**: Leverage Gemma 3 for intelligent document processing
- **Billing and Invoicing**: Track time, expenses, and generate invoices

## AI Services

The system includes AI capabilities powered by Gemma 3 open-source models:

- **Document Analysis**: Analyze legal documents using Gemma 3
- **Semantic Search**: Search for documents using natural language
- **Vector Embeddings**: Store and search document embeddings
- **Prompt Templates**: Manage templates for different legal tasks

## Recent Improvements

- Implemented service factory pattern for AI services
- Added fallback mechanisms to use mock services when real services fail
- Improved error handling and logging
- Enhanced model selection to prioritize gemma-3-12b-it-qat
- Added clear indication when mock responses are being used
