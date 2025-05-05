"""
URL configuration for API v1.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views import (
    PracticeAreaViewSet, CourtViewSet, ClientViewSet,
    CaseViewSet, CaseNoteViewSet, CaseEventViewSet,
    DocumentViewSet, AIAnalysisRequestViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'practice-areas', PracticeAreaViewSet)
router.register(r'courts', CourtViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'cases', CaseViewSet)
router.register(r'case-notes', CaseNoteViewSet)
router.register(r'case-events', CaseEventViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'ai-analysis', AIAnalysisRequestViewSet)

# Create schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Legal Case Management API",
        default_version='v1',
        description="API documentation for the Legal Case Management System",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

app_name = 'api_v1'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # API documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
]
