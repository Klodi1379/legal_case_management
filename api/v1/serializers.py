"""
Serializers for API v1.
"""
from rest_framework import serializers
from cases.models import Case, CaseNote, CaseEvent, PracticeArea, Court
from clients.models import Client
from documents.models import Document, DocumentVersion
from ai_services.models import AIAnalysisRequest, AIAnalysisResult


class PracticeAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeArea
        fields = ['id', 'name', 'description']


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'name', 'jurisdiction', 'address', 'phone', 'website', 'notes']


class ClientSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone', 'address', 'city', 'state',
            'zip_code', 'country', 'company_name', 'website', 'notes',
            'is_active', 'created_by', 'created_by_name', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class CaseSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    assigned_attorney_name = serializers.CharField(source='assigned_attorney.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    practice_area_name = serializers.CharField(source='practice_area.name', read_only=True)
    court_name = serializers.CharField(source='court.name', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id', 'title', 'case_number', 'internal_reference', 'client', 'client_name',
            'practice_area', 'practice_area_name', 'status', 'status_display',
            'case_type', 'description', 'priority', 'priority_display',
            'open_date', 'close_date', 'statute_of_limitations',
            'court', 'court_name', 'court_case_number', 'judge', 'opposing_counsel',
            'is_billable', 'billing_method', 'retainer_amount',
            'assigned_attorney', 'assigned_attorney_name', 'assigned_paralegal',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class CaseNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = CaseNote
        fields = [
            'id', 'case', 'author', 'author_name', 'title', 'content',
            'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']


class CaseEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = CaseEvent
        fields = [
            'id', 'case', 'title', 'event_type', 'description', 'date',
            'time', 'location', 'is_critical', 'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'case', 'case_title', 'title', 'description', 'file',
            'document_type', 'is_confidential', 'tags', 'uploaded_by',
            'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'document', 'version_number', 'file', 'comment',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'version_number']


class AIAnalysisRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    llm_model_name = serializers.CharField(source='llm_model.name', read_only=True)
    
    class Meta:
        model = AIAnalysisRequest
        fields = [
            'id', 'analysis_type', 'analysis_type_display', 'llm_model',
            'llm_model_name', 'prompt_template', 'document', 'case',
            'input_text', 'combined_prompt', 'custom_instructions',
            'context_items', 'requested_by', 'status', 'status_display',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['requested_by', 'status', 'created_at', 'completed_at']


class AIAnalysisResultSerializer(serializers.ModelSerializer):
    analysis_request_id = serializers.IntegerField(source='analysis_request.id', read_only=True)
    
    class Meta:
        model = AIAnalysisResult
        fields = [
            'id', 'analysis_request', 'analysis_request_id', 'output_text',
            'raw_response', 'tokens_used', 'processing_time', 'has_error',
            'error_message', 'created_at'
        ]
        read_only_fields = ['created_at']
