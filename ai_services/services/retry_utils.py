"""
Retry utilities for AI services.

This module provides utilities for retrying operations with
exponential backoff and other retry strategies.
"""

import time
import logging
import random
from functools import wraps
from typing import Callable, Type, List, Optional, Any, Dict, Union
from .exceptions import AIServiceException, ServiceConnectionError, ServiceTimeoutError

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions_to_retry: List[Type[Exception]] = None
):
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to multiply delay by after each retry
        jitter: Whether to add random jitter to delay
        exceptions_to_retry: List of exception types to retry on
        
    Returns:
        Decorated function
    """
    if exceptions_to_retry is None:
        exceptions_to_retry = [ServiceConnectionError, ServiceTimeoutError]
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for retry in range(max_retries + 1):
                try:
                    if retry > 0:
                        logger.info(f"Retry {retry}/{max_retries} for {func.__name__} after {delay:.2f}s delay")
                    return func(*args, **kwargs)
                except tuple(exceptions_to_retry) as e:
                    last_exception = e
                    
                    if retry >= max_retries:
                        logger.warning(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise
                        
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
                    
                    # Add jitter if enabled (±20% of delay)
                    if jitter:
                        delay = delay * (1 + random.uniform(-0.2, 0.2))
                        
                    # Log the exception and retry
                    logger.warning(f"Exception in {func.__name__}: {str(e)}. Retrying in {delay:.2f}s...")
                    
                    # Wait before retrying
                    time.sleep(delay)
            
            # This should never be reached due to the raise in the loop
            raise last_exception or RuntimeError("Unexpected error in retry logic")
            
        return wrapper
    return decorator


class RetryContext:
    """
    Context for tracking retry attempts.
    
    This class is used to track retry attempts and provide
    context for retry decisions.
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 10.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.attempts = 0
        self.delay = initial_delay
        self.exceptions = []
        
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if another retry should be attempted.
        
        Args:
            exception: The exception that was raised
            
        Returns:
            True if another retry should be attempted, False otherwise
        """
        self.exceptions.append(exception)
        self.attempts += 1
        
        # Check if we've reached the maximum number of retries
        if self.attempts > self.max_retries:
            return False
            
        # Check if the exception is retryable
        if isinstance(exception, (ServiceConnectionError, ServiceTimeoutError)):
            return True
            
        # Don't retry other exceptions
        return False
        
    def get_next_delay(self) -> float:
        """
        Get the delay before the next retry attempt.
        
        Returns:
            Delay in seconds
        """
        # Calculate next delay with exponential backoff
        self.delay = min(self.delay * self.backoff_factor, self.max_delay)
        
        # Add jitter if enabled (±20% of delay)
        if self.jitter:
            self.delay = self.delay * (1 + random.uniform(-0.2, 0.2))
            
        return self.delay
