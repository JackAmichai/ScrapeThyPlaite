"""
Retry Handler - Intelligent retry logic with exponential backoff.
"""

import asyncio
from typing import Optional, Callable, Any, Type, Tuple
from functools import wraps
import random

from loguru import logger

from scrape_thy_plaite.core.config import RetryConfig
from scrape_thy_plaite.core.exceptions import RetryExhaustedError


class RetryHandler:
    """
    Handle retries with configurable backoff strategies.
    
    Features:
    - Exponential backoff
    - Jitter to prevent thundering herd
    - Configurable retry conditions
    - Status code and exception filtering
    
    Example:
        handler = RetryHandler(config)
        
        @handler.retry
        async def fetch_data():
            # Your code here
            pass
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.config.initial_delay * (self.config.backoff_factor ** attempt)
        delay = min(delay, self.config.max_delay)
        
        # Add jitter (±25%)
        jitter = delay * 0.25
        delay = delay + random.uniform(-jitter, jitter)
        
        return max(0, delay)
    
    def _should_retry(
        self, 
        exception: Optional[Exception] = None,
        status_code: Optional[int] = None
    ) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            exception: The exception that was raised
            status_code: HTTP status code if applicable
            
        Returns:
            True if should retry, False otherwise
        """
        if status_code is not None:
            if status_code in self.config.retry_on_status_codes:
                return True
        
        if exception is not None:
            exception_name = type(exception).__name__
            if exception_name in self.config.retry_on_exceptions:
                return True
            
            # Also check parent classes
            for exc_name in self.config.retry_on_exceptions:
                if exc_name in str(type(exception).__mro__):
                    return True
        
        return False
    
    def retry(self, func: Callable) -> Callable:
        """
        Decorator to add retry logic to a function.
        
        Args:
            func: Async function to wrap
            
        Returns:
            Wrapped function with retry logic
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if not self._should_retry(exception=e):
                        raise
                    
                    if attempt < self.config.max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {self.config.max_retries + 1} attempts failed"
                        )
                        raise RetryExhaustedError(
                            f"Retry exhausted after {self.config.max_retries + 1} attempts",
                            attempts=self.config.max_retries + 1,
                            last_error=last_exception
                        )
            
            raise RetryExhaustedError(
                f"Retry exhausted",
                attempts=self.config.max_retries + 1,
                last_error=last_exception
            )
        
        return wrapper
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        @self.retry
        async def wrapped():
            return await func(*args, **kwargs)
        
        return await wrapped()


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator factory for retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries
        backoff_factor: Multiplier for exponential backoff
        max_delay: Maximum delay between retries
        retry_on: Tuple of exception types to retry on
        
    Example:
        @with_retry(max_retries=3, retry_on=(ConnectionError, TimeoutError))
        async def fetch_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = min(
                            initial_delay * (backoff_factor ** attempt),
                            max_delay
                        )
                        # Add jitter
                        delay = delay + random.uniform(0, delay * 0.1)
                        
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise RetryExhaustedError(
                            f"All {max_retries + 1} attempts failed",
                            attempts=max_retries + 1,
                            last_error=last_exception
                        )
            
            raise last_exception
        
        return wrapper
    return decorator
