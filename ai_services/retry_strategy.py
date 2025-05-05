"""
Retry strategies for AI service calls.

Provides exponential backoff and retry logic for transient failures.
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional
from core.exceptions import AIServiceException

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (AIServiceException,)
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter to delays
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after error: {str(e)}. Waiting {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
                except Exception as e:
                    # Re-raise non-retryable exceptions
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def retry_with_timeout(
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Callable:
    """
    Decorator that implements retry logic with timeout.
    
    Args:
        timeout: Total timeout for all retries in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None
            
            for attempt in range(max_retries + 1):
                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Timeout of {timeout}s exceeded for {func.__name__}"
                    )
                
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        time_left = timeout - (time.time() - start_time)
                        delay = min(retry_delay, time_left)
                        
                        if delay > 0:
                            logger.warning(
                                f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                                f"after error: {str(e)}. Waiting {delay:.2f}s"
                            )
                            time.sleep(delay)
                        else:
                            break
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryableError(Exception):
    """Base class for errors that should trigger retries."""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should not trigger retries."""
    pass
