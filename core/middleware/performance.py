"""
Performance optimization middleware.
"""
import time
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.cache import get_cache_key, patch_response_headers
from django.utils.deprecation import MiddlewareMixin
from core.utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor request performance and log slow requests.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.slow_request_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)  # 1 second
    
    def process_request(self, request):
        """Start timing the request."""
        request._start_time = time.time()
    
    def process_response(self, request, response):
        """Log request duration and warn about slow requests."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    "Slow request detected",
                    path=request.path,
                    method=request.method,
                    duration=f"{duration:.3f}s",
                    user_id=request.user.id if request.user.is_authenticated else None,
                    status_code=response.status_code
                )
            
            # Add timing header in development
            if settings.DEBUG:
                response['X-Request-Duration'] = f"{duration:.3f}s"
        
        return response


class CacheMiddleware(MiddlewareMixin):
    """
    Custom cache middleware for specific views.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        # Define cache settings for specific paths
        self.cache_settings = {
            '/api/v1/practice-areas/': {'timeout': 3600, 'key_prefix': 'practice_areas'},
            '/api/v1/courts/': {'timeout': 3600, 'key_prefix': 'courts'},
            '/static/': {'timeout': 86400, 'key_prefix': 'static'},
        }
    
    def process_request(self, request):
        """Try to serve from cache for GET requests."""
        if request.method != 'GET':
            return None
        
        # Check if path should be cached
        for path_prefix, settings in self.cache_settings.items():
            if request.path.startswith(path_prefix):
                # Generate cache key
                cache_key = self._generate_cache_key(request, settings['key_prefix'])
                
                # Try to get from cache
                cached_response = cache.get(cache_key)
                if cached_response:
                    logger.debug(
                        "Cache hit",
                        path=request.path,
                        cache_key=cache_key
                    )
                    return cached_response
                
                # Store cache key for later use
                request._cache_key = cache_key
                request._cache_timeout = settings['timeout']
                break
        
        return None
    
    def process_response(self, request, response):
        """Cache successful responses."""
        if (hasattr(request, '_cache_key') and 
            response.status_code == 200 and 
            request.method == 'GET'):
            
            # Only cache if response is cacheable
            if not response.has_header('Cache-Control'):
                patch_response_headers(response, request._cache_timeout)
            
            # Store in cache
            cache.set(request._cache_key, response, request._cache_timeout)
            
            logger.debug(
                "Response cached",
                path=request.path,
                cache_key=request._cache_key,
                timeout=request._cache_timeout
            )
        
        return response
    
    def _generate_cache_key(self, request, key_prefix):
        """Generate a cache key for the request."""
        # Include query parameters in cache key
        query_string = request.META.get('QUERY_STRING', '')
        if query_string:
            key = f"{key_prefix}:{request.path}?{query_string}"
        else:
            key = f"{key_prefix}:{request.path}"
        
        # Include user ID for authenticated requests
        if request.user.is_authenticated:
            key = f"{key}:user_{request.user.id}"
        
        return key


class CompressionMiddleware(MiddlewareMixin):
    """
    Compress response content for better performance.
    """
    
    def process_response(self, request, response):
        """Compress response if client supports it."""
        # Check if client accepts gzip
        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' not in ae.lower():
            return response
        
        # Check if response is already compressed
        if response.has_header('Content-Encoding'):
            return response
        
        # Only compress certain content types
        content_type = response.get('Content-Type', '').lower()
        compressible_types = ['text/', 'application/json', 'application/javascript']
        
        if not any(t in content_type for t in compressible_types):
            return response
        
        # Don't compress small responses
        if len(response.content) < 200:
            return response
        
        # Compress response
        import gzip
        compressed_content = gzip.compress(response.content)
        
        # Only use compression if it actually reduces size
        if len(compressed_content) < len(response.content):
            response.content = compressed_content
            response['Content-Encoding'] = 'gzip'
            response['Content-Length'] = str(len(compressed_content))
        
        return response


class DatabaseQueryMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor database queries in development.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.query_threshold = getattr(settings, 'QUERY_COUNT_THRESHOLD', 20)
    
    def process_request(self, request):
        """Reset query counter."""
        if settings.DEBUG:
            from django.db import reset_queries
            reset_queries()
    
    def process_response(self, request, response):
        """Log query count and warn about excessive queries."""
        if settings.DEBUG:
            from django.db import connection
            
            query_count = len(connection.queries)
            
            if query_count > self.query_threshold:
                logger.warning(
                    "Excessive database queries detected",
                    path=request.path,
                    method=request.method,
                    query_count=query_count,
                    threshold=self.query_threshold
                )
            
            # Add query count header in development
            response['X-DB-Query-Count'] = str(query_count)
            
            # Log slow queries
            for query in connection.queries:
                if float(query['time']) > 0.1:  # 100ms threshold
                    logger.warning(
                        "Slow database query detected",
                        sql=query['sql'],
                        time=query['time']
                    )
        
        return response
