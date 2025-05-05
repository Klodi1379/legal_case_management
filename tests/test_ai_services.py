"""
Test cases for AI services.
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from ai_services.models import LLMModel, PromptTemplate, AIAnalysisRequest, AIAnalysisResult
from ai_services.circuit_breaker import CircuitBreaker, CircuitBreakerState
from ai_services.retry_strategy import exponential_backoff, retry_with_timeout
from core.exceptions import AIServiceException
from accounts.models import User
import time


class CircuitBreakerTests(TestCase):
    """Test cases for circuit breaker functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1,
            half_open_max_calls=2
        )
    
    def test_circuit_breaker_initial_state(self):
        """Test initial state of circuit breaker."""
        self.assertEqual(self.circuit_breaker.state.state, "CLOSED")
        self.assertEqual(self.circuit_breaker.state.failure_count, 0)
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        @self.circuit_breaker
        def failing_function():
            raise AIServiceException("Test failure")
        
        # Trigger failures
        for _ in range(3):
            with self.assertRaises(AIServiceException):
                failing_function()
        
        self.assertEqual(self.circuit_breaker.state.state, "OPEN")
        self.assertEqual(self.circuit_breaker.state.failure_count, 3)
    
    def test_circuit_breaker_blocks_calls_when_open(self):
        """Test circuit breaker blocks calls when open."""
        @self.circuit_breaker
        def test_function():
            return "success"
        
        # Force open state
        self.circuit_breaker.state.state = "OPEN"
        self.circuit_breaker.state.failure_count = 5
        
        with self.assertRaises(AIServiceException):
            test_function()
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery cycle."""
        @self.circuit_breaker
        def test_function(should_fail=False):
            if should_fail:
                raise AIServiceException("Test failure")
            return "success"
        
        # Force open state
        self.circuit_breaker.state.state = "OPEN"
        self.circuit_breaker.state.last_failure_time = None
        
        # Should move to HALF_OPEN
        result = test_function(should_fail=False)
        self.assertEqual(result, "success")
        self.assertEqual(self.circuit_breaker.state.state, "HALF_OPEN")
        
        # Additional successful calls should close the circuit
        test_function(should_fail=False)
        self.assertEqual(self.circuit_breaker.state.state, "CLOSED")


class RetryStrategyTests(TestCase):
    """Test cases for retry strategies."""
    
    def test_exponential_backoff_success(self):
        """Test exponential backoff with successful retry."""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise AIServiceException("Temporary failure")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)
    
    def test_exponential_backoff_max_retries(self):
        """Test exponential backoff hits max retries."""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise AIServiceException("Persistent failure")
        
        with self.assertRaises(AIServiceException):
            test_function()
        
        self.assertEqual(call_count, 4)  # Original + 3 retries
    
    def test_retry_with_timeout(self):
        """Test retry with timeout functionality."""
        call_count = 0
        
        @retry_with_timeout(timeout=1.0, max_retries=5, retry_delay=0.3)
        def test_function():
            nonlocal call_count
            call_count += 1
            time.sleep(0.2)
            raise Exception("Test failure")
        
        with self.assertRaises(TimeoutError):
            test_function()
        
        # Should have made fewer calls due to timeout
        self.assertLess(call_count, 5)


class AIModelsTests(TestCase):
    """Test cases for AI model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.llm_model = LLMModel.objects.create(
            name='Test LLM',
            model_type='gemma_3',
            model_version='3-12b-it-qat',
            deployment_type='api',
            endpoint_url='http://localhost:1234/v1/chat/completions',
            is_active=True
        )
        
        self.prompt_template = PromptTemplate.objects.create(
            name='Test Template',
            task_type='document_summarization',
            prompt_template='Summarize the following document: {document}',
            system_prompt='You are a legal document summarizer.',
            created_by=self.user,
            is_active=True
        )
    
    def test_llm_model_creation(self):
        """Test LLM model creation."""
        self.assertEqual(str(self.llm_model), 'Test LLM (gemma_3-3-12b-it-qat)')
        self.assertTrue(self.llm_model.is_active)
    
    def test_prompt_template_creation(self):
        """Test prompt template creation."""
        self.assertEqual(str(self.prompt_template), 'Test Template (document_summarization)')
        self.assertTrue(self.prompt_template.is_active)
    
    def test_ai_analysis_request_creation(self):
        """Test AI analysis request creation."""
        analysis_request = AIAnalysisRequest.objects.create(
            analysis_type='DOCUMENT_SUMMARY',
            llm_model=self.llm_model,
            prompt_template=self.prompt_template,
            input_text='Test document content',
            combined_prompt='Summarize: Test document content',
            requested_by=self.user,
            status='PENDING'
        )
        
        self.assertEqual(analysis_request.status, 'PENDING')
        self.assertEqual(analysis_request.analysis_type, 'DOCUMENT_SUMMARY')
    
    def test_ai_analysis_result_creation(self):
        """Test AI analysis result creation."""
        analysis_request = AIAnalysisRequest.objects.create(
            analysis_type='DOCUMENT_SUMMARY',
            llm_model=self.llm_model,
            prompt_template=self.prompt_template,
            input_text='Test document content',
            combined_prompt='Summarize: Test document content',
            requested_by=self.user,
            status='COMPLETED'
        )
        
        analysis_result = AIAnalysisResult.objects.create(
            analysis_request=analysis_request,
            output_text='This is a summary of the test document.',
            raw_response={'choices': [{'message': {'content': 'This is a summary of the test document.'}}]},
            tokens_used=100,
            processing_time=2.5,
            has_error=False
        )
        
        self.assertEqual(analysis_result.output_text, 'This is a summary of the test document.')
        self.assertFalse(analysis_result.has_error)
        self.assertEqual(analysis_result.tokens_used, 100)
