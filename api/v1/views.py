"""
API views for v1.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from cases.models import Case, CaseNote, CaseEvent, PracticeArea, Court
from clients.models import Client
from documents.models import Document, DocumentVersion
from ai_services.models import AIAnalysisRequest, AIAnalysisResult

from .serializers import (
    CaseSerializer, CaseNoteSerializer, CaseEventSerializer,
    PracticeAreaSerializer, CourtSerializer, ClientSerializer,
    DocumentSerializer, DocumentVersionSerializer,
    AIAnalysisRequestSerializer, AIAnalysisResultSerializer
)


class PracticeAreaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing practice areas.
    
    Practice areas are used to categorize legal cases by type of law.
    """
    queryset = PracticeArea.objects.all()
    serializer_class = PracticeAreaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class CourtViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing courts.
    
    Courts represent different judicial venues where cases are heard.
    """
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'jurisdiction', 'address']
    filterset_fields = ['jurisdiction']
    ordering_fields = ['name', 'jurisdiction']
    ordering = ['jurisdiction', 'name']


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing clients.
    
    Clients are individuals or organizations that the law firm represents.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'email', 'company_name']
    filterset_fields = ['is_active', 'city', 'state', 'country']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing legal cases.
    
    Cases represent legal matters that the firm is handling for clients.
    """
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'case_number', 'description']
    filterset_fields = ['status', 'case_type', 'priority', 'client', 'assigned_attorney']
    ordering_fields = ['open_date', 'priority', 'title']
    ordering = ['-open_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        method='post',
        operation_description="Close a case",
        responses={
            200: openapi.Response('Case closed successfully'),
            400: openapi.Response('Case already closed'),
        }
    )
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a case."""
        case = self.get_object()
        if case.status == 'CLOSED':
            return Response(
                {'error': 'Case is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        case.status = 'CLOSED'
        case.save()
        return Response({'status': 'Case closed successfully'})

    @swagger_auto_schema(
        method='post',
        operation_description="Reopen a closed case",
        responses={
            200: openapi.Response('Case reopened successfully'),
            400: openapi.Response('Case is not closed'),
        }
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a closed case."""
        case = self.get_object()
        if case.status != 'CLOSED':
            return Response(
                {'error': 'Case is not closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        case.status = 'OPEN'
        case.save()
        return Response({'status': 'Case reopened successfully'})

    @swagger_auto_schema(
        method='get',
        operation_description="Get case statistics",
        responses={
            200: openapi.Response(
                'Case statistics',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'open_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'closed_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'by_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'by_priority': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'by_type': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get case statistics."""
        from django.db.models import Count
        
        cases = self.get_queryset()
        
        stats = {
            'total_count': cases.count(),
            'open_count': cases.filter(status='OPEN').count(),
            'closed_count': cases.filter(status='CLOSED').count(),
            'by_status': dict(cases.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_priority': dict(cases.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_type': dict(cases.values('case_type').annotate(count=Count('id')).values_list('case_type', 'count')),
        }
        
        return Response(stats)


class CaseNoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing case notes.
    
    Notes can be attached to cases to track important information and updates.
    """
    queryset = CaseNote.objects.all()
    serializer_class = CaseNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['case', 'author', 'is_private']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter private notes based on user permissions
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_private=False)
        return queryset


class CaseEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing case events.
    
    Events track important dates and activities related to cases.
    """
    queryset = CaseEvent.objects.all()
    serializer_class = CaseEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['case', 'event_type', 'is_critical']
    ordering_fields = ['date', 'time']
    ordering = ['date', 'time']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        method='get',
        operation_description="Get upcoming events",
        responses={200: CaseEventSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events."""
        from django.utils import timezone
        today = timezone.now().date()
        
        upcoming_events = self.get_queryset().filter(date__gte=today).order_by('date', 'time')[:10]
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing documents.
    
    Documents can be uploaded and associated with cases.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'description', 'tags']
    filterset_fields = ['case', 'document_type', 'is_confidential']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class AIAnalysisRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing AI analysis requests.
    
    This endpoint allows creation and monitoring of AI analysis tasks.
    """
    queryset = AIAnalysisRequest.objects.all()
    serializer_class = AIAnalysisRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status', 'analysis_type', 'case', 'document']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @swagger_auto_schema(
        method='post',
        operation_description="Start AI analysis processing",
        responses={
            200: openapi.Response('Analysis started'),
            400: openapi.Response('Analysis already processed'),
        }
    )
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Start processing an AI analysis request."""
        analysis_request = self.get_object()
        
        if analysis_request.status != 'PENDING':
            return Response(
                {'error': 'Analysis request is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate with actual AI processing service
        # For now, just update the status
        analysis_request.status = 'PROCESSING'
        analysis_request.save()
        
        return Response({'status': 'Analysis processing started'})
