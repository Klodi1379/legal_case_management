# ai_services/urls.py
from django.urls import path
from . import views
from . import views_admin

app_name = 'ai_services'

urlpatterns = [
    # Dashboard
    path('', views.ai_dashboard, name='dashboard'),

    # Document Analysis
    path('documents/<int:document_id>/analyze/', views.document_analysis, name='document_analysis'),
    path('documents/<int:document_id>/submit-analysis/', views.submit_analysis, name='submit_analysis'),
    path('analysis/<int:analysis_id>/', views.analysis_result, name='analysis_result'),

    # Legal Research
    path('legal-research/', views.legal_research, name='legal_research'),
    path('legal-research/submit/', views.submit_research, name='submit_research'),

    # Document Generation
    path('document-generation/', views.document_generation, name='document_generation'),
    path('document-generation/submit/', views.submit_document_generation, name='submit_document_generation'),

    # Semantic Search
    path('semantic-search/', views.semantic_search, name='semantic_search'),
    path('semantic-search/submit/', views.submit_semantic_search, name='submit_semantic_search'),

    # Admin/Management
    path('models/', views.model_list, name='model_list'),
    path('models/create/', views.model_create, name='model_create'),
    path('models/<int:model_id>/edit/', views.model_edit, name='model_edit'),
    path('models/<int:model_id>/delete/', views.model_delete, name='model_delete'),

    path('prompts/', views.prompt_list, name='prompt_list'),
    path('prompts/create/', views.prompt_create, name='prompt_create'),
    path('prompts/<int:prompt_id>/edit/', views.prompt_edit, name='prompt_edit'),
    path('prompts/<int:prompt_id>/delete/', views.prompt_delete, name='prompt_delete'),

    path('vector-stores/', views.vector_store_list, name='vector_store_list'),
    path('vector-stores/create/', views.vector_store_create, name='vector_store_create'),
    path('vector-stores/<int:store_id>/edit/', views.vector_store_edit, name='vector_store_edit'),
    path('vector-stores/<int:store_id>/delete/', views.vector_store_delete, name='vector_store_delete'),

    # Service Health Monitoring
    path('admin/service-health/', views_admin.service_health_dashboard, name='service_health'),
    path('admin/service-health/api/', views_admin.service_health_api, name='service_health_api'),
    path('admin/test-connection/<int:model_id>/', views_admin.test_service_connection, name='test_service_connection'),
]
