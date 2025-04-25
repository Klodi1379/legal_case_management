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

## Installation

To run this project locally, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/legal-case-management-system.git
    cd legal-case-management-system
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows, use `env\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Apply migrations**:
    ```bash
    python manage.py migrate
    ```

5. **Create a superuser**:
    ```bash
    python manage.py createsuperuser
    ```

6. **Run the development server**:
    ```bash
    python manage.py runserver
    ```

Visit `http://127.0.0.1:8000` to view the application.

## Usage

After installing and running the server, you can:

- Register a new user or log in with an existing account.
- Navigate through the dashboard to manage clients, cases, documents, and billing.
- Access the admin panel using the superuser account to manage all aspects of the application.
