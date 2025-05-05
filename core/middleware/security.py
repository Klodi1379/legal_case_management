"""
Security middleware for the legal case management system.
"""
import re
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from core.utils.logging import StructuredLogger
from core.utils.audit import audit_login, audit_logout

logger = StructuredLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request, response):
        """Add security headers to the response."""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.example.com;"
        )
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Strict Transport Security (only in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class IPWhitelistMiddleware(MiddlewareMixin):
    """
    Restrict access to whitelisted IP addresses for admin area.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
        self.admin_path = reverse('admin:index')
    
    def process_request(self, request):
        """Check if request is from whitelisted IP for admin access."""
        if request.path.startswith(self.admin_path):
            ip = self.get_client_ip(request)
            
            if self.whitelist and ip not in self.whitelist:
                logger.warning(
                    "Admin access attempted from non-whitelisted IP",
                    ip_address=ip,
                    path=request.path,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                raise PermissionDenied("Access denied from your IP address")
    
    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware for login attempts.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache = {}
        self.max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'LOGIN_LOCKOUT_DURATION', 300)  # 5 minutes
    
    def process_request(self, request):
        """Check rate limit for login attempts."""
        if request.path == reverse('accounts:login') and request.method == 'POST':
            ip = IPWhitelistMiddleware.get_client_ip(request)
            key = f'login_attempts_{ip}'
            
            # Check if IP is locked out
            if key in self.cache:
                attempts, last_attempt = self.cache[key]
                
                # Check if lockout period has expired
                import time
                if attempts >= self.max_attempts:
                    if time.time() - last_attempt < self.lockout_duration:
                        logger.warning(
                            "Rate limit exceeded for login attempts",
                            ip_address=ip,
                            attempts=attempts
                        )
                        raise PermissionDenied(
                            f"Too many login attempts. Please try again in {self.lockout_duration // 60} minutes."
                        )
                    else:
                        # Reset counter after lockout period
                        self.cache[key] = (0, time.time())
    
    def process_response(self, request, response):
        """Update rate limit counter after login attempt."""
        if request.path == reverse('accounts:login') and request.method == 'POST':
            ip = IPWhitelistMiddleware.get_client_ip(request)
            key = f'login_attempts_{ip}'
            
            import time
            current_time = time.time()
            
            # Update attempt counter
            if key in self.cache:
                attempts, _ = self.cache[key]
                self.cache[key] = (attempts + 1, current_time)
            else:
                self.cache[key] = (1, current_time)
            
            # Log login attempt
            if hasattr(request, 'user') and request.user.is_authenticated:
                audit_login(
                    user=request.user,
                    success=True,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            elif response.status_code == 200:  # Failed login
                # Try to get username from POST data
                username = request.POST.get('username', 'unknown')
                logger.info(
                    "Failed login attempt",
                    username=username,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
        
        return response


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    Additional XSS protection middleware.
    """
    
    # Patterns that might indicate XSS attempts
    XSS_PATTERNS = [
        r'<script\b[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'onload=',
        r'onerror=',
        r'onclick=',
        r'onmouseover=',
    ]
    
    def process_request(self, request):
        """Check request data for potential XSS patterns."""
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Check POST data
            for key, value in request.POST.items():
                if isinstance(value, str) and self._contains_xss_pattern(value):
                    logger.warning(
                        "Potential XSS attempt detected",
                        field=key,
                        ip_address=IPWhitelistMiddleware.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    raise PermissionDenied("Invalid input detected")
    
    def _contains_xss_pattern(self, value):
        """Check if value contains XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced session security middleware.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.session_timeout = getattr(settings, 'SESSION_SECURITY_TIMEOUT', 3600)  # 1 hour
    
    def process_request(self, request):
        """Check session security and timeout."""
        if request.user.is_authenticated:
            # Check for session timeout
            last_activity = request.session.get('last_activity')
            import time
            current_time = time.time()
            
            if last_activity:
                if current_time - last_activity > self.session_timeout:
                    # Session expired
                    logger.info(
                        "Session expired due to inactivity",
                        user_id=request.user.id,
                        username=request.user.username
                    )
                    from django.contrib.auth import logout
                    logout(request)
                    return
            
            # Update last activity time
            request.session['last_activity'] = current_time
            
            # Regenerate session ID periodically
            if not request.session.get('session_regenerated'):
                request.session.cycle_key()
                request.session['session_regenerated'] = True
