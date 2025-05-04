"""
Admin views for AI services.

This module provides views for managing AI services, including
monitoring service health and performance.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import LLMModel, VectorStore, AISettings
from .services.service_factory import AIServiceFactory
from .services.service_monitor import ServiceMonitor

logger = logging.getLogger(__name__)

def is_staff(user):
    """Check if user is staff."""
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def service_health_dashboard(request):
    """
    Dashboard for monitoring AI service health.
    
    This view displays the health status of all AI services,
    including error rates, response times, and other metrics.
    """
    # Get health status for all services
    services_health = ServiceMonitor.get_all_services_health()
    
    # Get all configured models
    llm_models = LLMModel.objects.all()
    vector_stores = VectorStore.objects.all()
    
    # Get performance metrics for each service
    performance_metrics = {}
    for service_name in services_health.keys():
        performance_metrics[service_name] = ServiceMonitor.get_service_performance(service_name)
    
    context = {
        'services_health': services_health,
        'performance_metrics': performance_metrics,
        'llm_models': llm_models,
        'vector_stores': vector_stores,
        'last_updated': timezone.now(),
    }
    
    return render(request, 'ai_services/service_health.html', context)

@login_required
@user_passes_test(is_staff)
def service_health_api(request):
    """
    API endpoint for service health data.
    
    This view returns JSON data about service health for use in
    dashboards and monitoring tools.
    """
    # Get health status for all services
    services_health = ServiceMonitor.get_all_services_health()
    
    # Get performance metrics for each service
    performance_metrics = {}
    for service_name in services_health.keys():
        performance_metrics[service_name] = ServiceMonitor.get_service_performance(service_name)
    
    data = {
        'services_health': services_health,
        'performance_metrics': performance_metrics,
        'last_updated': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)

@login_required
@user_passes_test(is_staff)
def test_service_connection(request, model_id):
    """
    Test connection to an AI service.
    
    This view tests the connection to an AI service and returns
    the result as JSON.
    """
    try:
        model = LLMModel.objects.get(id=model_id)
        
        # Create a service instance with no fallback
        service = AIServiceFactory.get_llm_service(
            model_instance=model,
            use_mock_fallback=False,
            check_health=False
        )
        
        # Try a simple prompt to test the connection
        result = service.generate_text(
            prompt="This is a test prompt to check if the service is working. Please respond with 'Service is working'.",
            system_prompt="You are a helpful assistant."
        )
        
        # Check if there was an error
        if result.get("error"):
            return JsonResponse({
                'success': False,
                'message': f"Connection failed: {result['error']}",
                'details': result
            })
        
        return JsonResponse({
            'success': True,
            'message': "Connection successful",
            'response': result.get("text", "")[:100] + "...",
            'processing_time': f"{result.get('processing_time', 0):.2f}s",
            'tokens_used': result.get("tokens_used", 0)
        })
        
    except LLMModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f"Model with ID {model_id} not found"
        })
        
    except Exception as e:
        logger.error(f"Error testing service connection: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f"Error: {str(e)}"
        })
