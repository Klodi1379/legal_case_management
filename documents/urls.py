# documents/urls.py
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document URLs
    path('upload/', views.document_upload, name='document_upload'),
    path('recent/', views.recent_documents, name='recent_documents'),
    path('<int:case_id>/', views.document_list, name='document_list'),
    path('delete/<int:document_id>/', views.document_delete, name='document_delete'),

    # Document Template URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/upload/', views.template_upload, name='template_upload'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:template_id>/download/', views.template_download, name='template_download'),
]