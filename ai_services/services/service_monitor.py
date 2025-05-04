"""
Service monitoring for AI services.

This module provides functionality for monitoring the health and performance
of AI services, tracking errors, and providing diagnostics.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class ServiceMonitor:
    """
    Monitor for tracking AI service health and performance.
    
    This class provides methods for tracking service calls, errors,
    and performance metrics. It uses Django's cache to store
    short-term metrics and can be extended to store long-term
    metrics in the database.
    """
    
    # Cache keys
    HEALTH_STATUS_KEY = "ai_service_health:{service_name}"
    ERROR_COUNT_KEY = "ai_service_errors:{service_name}:{error_type}"
    PERFORMANCE_KEY = "ai_service_performance:{service_name}"
    
    # Status constants
    STATUS_HEALTHY = "healthy"
    STATUS_DEGRADED = "degraded"
    STATUS_UNHEALTHY = "unhealthy"
    
    @classmethod
    def record_service_call(cls, service_name: str, endpoint: str, 
                           success: bool, response_time: float,
                           error_type: Optional[str] = None,
                           error_message: Optional[str] = None) -> None:
        """
        Record a service call for monitoring purposes.
        
        Args:
            service_name: Name of the service (e.g., "GemmaService")
            endpoint: Endpoint URL
            success: Whether the call was successful
            response_time: Response time in seconds
            error_type: Type of error if the call failed
            error_message: Error message if the call failed
        """
        # Update health status
        health_key = cls.HEALTH_STATUS_KEY.format(service_name=service_name)
        performance_key = cls.PERFORMANCE_KEY.format(service_name=service_name)
        
        # Get current health status
        health_status = cache.get(health_key, {
            "status": cls.STATUS_HEALTHY,
            "last_checked": timezone.now().isoformat(),
            "last_error": None,
            "consecutive_errors": 0,
            "total_calls": 0,
            "successful_calls": 0,
            "error_calls": 0
        })
        
        # Update health status
        health_status["total_calls"] += 1
        health_status["last_checked"] = timezone.now().isoformat()
        
        if success:
            health_status["successful_calls"] += 1
            health_status["consecutive_errors"] = 0
        else:
            health_status["error_calls"] += 1
            health_status["consecutive_errors"] += 1
            health_status["last_error"] = {
                "type": error_type,
                "message": error_message,
                "timestamp": timezone.now().isoformat()
            }
            
            # Update error count
            if error_type:
                error_key = cls.ERROR_COUNT_KEY.format(
                    service_name=service_name,
                    error_type=error_type
                )
                error_count = cache.get(error_key, 0)
                cache.set(error_key, error_count + 1, timeout=3600)  # 1 hour timeout
        
        # Determine health status based on error rate and consecutive errors
        error_rate = health_status["error_calls"] / health_status["total_calls"]
        if health_status["consecutive_errors"] >= 5 or error_rate > 0.5:
            health_status["status"] = cls.STATUS_UNHEALTHY
        elif health_status["consecutive_errors"] >= 2 or error_rate > 0.2:
            health_status["status"] = cls.STATUS_DEGRADED
        else:
            health_status["status"] = cls.STATUS_HEALTHY
            
        # Save updated health status
        cache.set(health_key, health_status, timeout=3600)  # 1 hour timeout
        
        # Update performance metrics
        performance_data = cache.get(performance_key, {
            "response_times": [],
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0
        })
        
        # Add new response time (keep last 100)
        performance_data["response_times"].append(response_time)
        if len(performance_data["response_times"]) > 100:
            performance_data["response_times"].pop(0)
            
        # Update stats
        if performance_data["response_times"]:
            performance_data["avg_response_time"] = sum(performance_data["response_times"]) / len(performance_data["response_times"])
            performance_data["min_response_time"] = min(performance_data["response_times"])
            performance_data["max_response_time"] = max(performance_data["response_times"])
            
        # Save updated performance data
        cache.set(performance_key, performance_data, timeout=3600)  # 1 hour timeout
        
        # Log the service call
        if success:
            logger.info(f"Service call to {service_name} succeeded in {response_time:.2f}s")
        else:
            logger.warning(f"Service call to {service_name} failed in {response_time:.2f}s: {error_type} - {error_message}")
    
    @classmethod
    def get_service_health(cls, service_name: str) -> Dict[str, Any]:
        """
        Get the current health status of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary with health status information
        """
        health_key = cls.HEALTH_STATUS_KEY.format(service_name=service_name)
        health_status = cache.get(health_key, {
            "status": cls.STATUS_HEALTHY,
            "last_checked": timezone.now().isoformat(),
            "last_error": None,
            "consecutive_errors": 0,
            "total_calls": 0,
            "successful_calls": 0,
            "error_calls": 0
        })
        return health_status
    
    @classmethod
    def get_service_performance(cls, service_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary with performance metrics
        """
        performance_key = cls.PERFORMANCE_KEY.format(service_name=service_name)
        performance_data = cache.get(performance_key, {
            "response_times": [],
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0
        })
        return performance_data
    
    @classmethod
    def get_all_services_health(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all monitored services.
        
        Returns:
            Dictionary mapping service names to health status
        """
        # This is a simplified implementation that would need to be
        # extended to track all services in a real application
        services = ["GemmaService", "VectorSearchService", "EmbeddingService"]
        result = {}
        
        for service_name in services:
            result[service_name] = cls.get_service_health(service_name)
            
        return result
