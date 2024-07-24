# documents/urls.py
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/', views.document_upload, name='document_upload'),
    path('recent/', views.recent_documents, name='recent_documents'),
    path('<int:case_id>/', views.document_list, name='document_list'),
    path('delete/<int:document_id>/', views.document_delete, name='document_delete'),
]