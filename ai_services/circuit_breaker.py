"""
Circuit breaker implementation for AI services.

Provides resilience and fault tolerance for external AI service calls.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from core.exceptions import AIServiceException

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Tracks circuit breaker state and metrics."""
    failure_count: int = 0
    last_failure_time: datetime = None
    last_success_time: datetime = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests are allowed
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitBreakerState()
        self.half_open_calls = 0
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit state
            if self.state.state == "OPEN":
                if self._should_try_half_open():
                    self.state.state = "HALF_OPEN"
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise AIServiceException(
                        f"Circuit breaker is OPEN for {func.__name__}. Service is unavailable."
                    )
            
            # Execute function
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                logger.error(f"Circuit breaker caught error in {func.__name__}: {str(e)}")
                raise
                
        return wrapper
    
    def _on_success(self):
        """Handle successful call."""
        self.state.last_success_time = datetime.now()
        
        if self.state.state == "HALF_OPEN":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Enough successful calls, close the circuit
                self.state.state = "CLOSED"
                self.state.failure_count = 0
                logger.info("Circuit breaker closed after successful recovery")
        else:
            # Reset failure count on success in CLOSED state
            self.state.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.state.failure_count += 1
        self.state.last_failure_time = datetime.now()
        
        if self.state.state == "HALF_OPEN":
            # Failure in HALF_OPEN state reopens the circuit
            self.state.state = "OPEN"
            logger.warning("Circuit breaker reopened after failure in HALF_OPEN state")
        elif self.state.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            self.state.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.state.failure_count} failures")
    
    def _should_try_half_open(self) -> bool:
        """Check if enough time has passed to try HALF_OPEN state."""
        if not self.state.last_failure_time:
            return True
            
        time_since_failure = datetime.now() - self.state.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout


# Create circuit breakers for different services
llm_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
embedding_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
