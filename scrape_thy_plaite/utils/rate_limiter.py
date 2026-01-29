"""
Rate Limiter - Control request rates to avoid overwhelming servers.
"""

import asyncio
from typing import Optional, Dict
from collections import defaultdict
from datetime import datetime, timedelta
import time

from loguru import logger

from scrape_thy_plaite.core.config import RateLimitConfig


class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates.
    
    Features:
    - Per-domain rate limiting
    - Burst support
    - Async-friendly
    - Configurable rates
    
    Example:
        limiter = RateLimiter(config)
        await limiter.acquire("example.com")  # Wait if needed
        # Make request...
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Token buckets per domain
        self._tokens: Dict[str, float] = defaultdict(lambda: self.config.burst_size)
        self._last_update: Dict[str, float] = defaultdict(time.time)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    def _get_rate(self, domain: str) -> float:
        """Get rate limit for a domain."""
        # Check domain-specific rate
        if domain in self.config.domain_specific:
            return self.config.domain_specific[domain]
        return self.config.requests_per_second
    
    def _update_tokens(self, domain: str) -> None:
        """Update available tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update[domain]
        self._last_update[domain] = now
        
        rate = self._get_rate(domain)
        new_tokens = elapsed * rate
        
        self._tokens[domain] = min(
            self.config.burst_size,
            self._tokens[domain] + new_tokens
        )
    
    async def acquire(self, domain: str, tokens: float = 1.0) -> None:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            domain: Domain to acquire tokens for
            tokens: Number of tokens to acquire (default 1)
        """
        if not self.config.enabled:
            return
        
        async with self._locks[domain]:
            while True:
                self._update_tokens(domain)
                
                if self._tokens[domain] >= tokens:
                    self._tokens[domain] -= tokens
                    return
                
                # Calculate wait time
                rate = self._get_rate(domain)
                needed = tokens - self._tokens[domain]
                wait_time = needed / rate
                
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
    
    def try_acquire(self, domain: str, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without waiting.
        
        Args:
            domain: Domain to acquire tokens for
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        if not self.config.enabled:
            return True
        
        self._update_tokens(domain)
        
        if self._tokens[domain] >= tokens:
            self._tokens[domain] -= tokens
            return True
        
        return False
    
    def get_wait_time(self, domain: str, tokens: float = 1.0) -> float:
        """
        Get estimated wait time for acquiring tokens.
        
        Args:
            domain: Domain to check
            tokens: Number of tokens needed
            
        Returns:
            Estimated wait time in seconds
        """
        if not self.config.enabled:
            return 0.0
        
        self._update_tokens(domain)
        
        if self._tokens[domain] >= tokens:
            return 0.0
        
        rate = self._get_rate(domain)
        needed = tokens - self._tokens[domain]
        return needed / rate
    
    def set_domain_rate(self, domain: str, rate: float) -> None:
        """
        Set a custom rate for a specific domain.
        
        Args:
            domain: Domain to configure
            rate: Requests per second
        """
        self.config.domain_specific[domain] = rate
        logger.info(f"Set rate limit for {domain}: {rate} req/s")
    
    def reset(self, domain: Optional[str] = None) -> None:
        """
        Reset rate limiter state.
        
        Args:
            domain: Specific domain to reset, or None for all
        """
        if domain:
            self._tokens[domain] = self.config.burst_size
            self._last_update[domain] = time.time()
        else:
            self._tokens.clear()
            self._last_update.clear()
        
        logger.debug(f"Rate limiter reset: {domain or 'all'}")


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for more precise rate limiting.
    
    Uses a sliding window approach instead of token bucket
    for more accurate rate enforcement.
    """
    
    def __init__(
        self,
        requests_per_second: float = 1.0,
        window_size: float = 1.0
    ):
        self.requests_per_second = requests_per_second
        self.window_size = window_size
        self._requests: Dict[str, list] = defaultdict(list)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def acquire(self, domain: str) -> None:
        """Acquire permission to make a request."""
        async with self._locks[domain]:
            now = time.time()
            window_start = now - self.window_size
            
            # Remove old requests outside the window
            self._requests[domain] = [
                t for t in self._requests[domain] 
                if t > window_start
            ]
            
            # Check if we're at the limit
            max_requests = int(self.requests_per_second * self.window_size)
            
            while len(self._requests[domain]) >= max_requests:
                # Calculate wait time
                oldest = self._requests[domain][0]
                wait_time = oldest + self.window_size - now + 0.01
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                now = time.time()
                window_start = now - self.window_size
                self._requests[domain] = [
                    t for t in self._requests[domain] 
                    if t > window_start
                ]
            
            # Record this request
            self._requests[domain].append(now)


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts based on server responses.
    
    Automatically slows down when receiving rate limit responses
    and speeds up when successful.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config)
        self._success_count: Dict[str, int] = defaultdict(int)
        self._error_count: Dict[str, int] = defaultdict(int)
        self._base_rates: Dict[str, float] = {}
    
    def report_success(self, domain: str) -> None:
        """Report a successful request."""
        self._success_count[domain] += 1
        self._error_count[domain] = 0
        
        # Gradually increase rate after consecutive successes
        if self._success_count[domain] >= 10:
            current_rate = self._get_rate(domain)
            base_rate = self._base_rates.get(domain, current_rate)
            
            if current_rate < base_rate:
                new_rate = min(current_rate * 1.1, base_rate)
                self.set_domain_rate(domain, new_rate)
                logger.debug(f"Increased rate for {domain}: {new_rate:.2f} req/s")
            
            self._success_count[domain] = 0
    
    def report_rate_limit(self, domain: str, retry_after: Optional[int] = None) -> None:
        """Report a rate limit response."""
        self._error_count[domain] += 1
        self._success_count[domain] = 0
        
        current_rate = self._get_rate(domain)
        
        # Store base rate if not stored
        if domain not in self._base_rates:
            self._base_rates[domain] = current_rate
        
        # Reduce rate
        new_rate = current_rate * 0.5
        self.set_domain_rate(domain, max(0.1, new_rate))
        
        logger.warning(
            f"Rate limit hit for {domain}. "
            f"Reduced rate to {new_rate:.2f} req/s"
        )
        
        if retry_after:
            logger.info(f"Retry-After header: {retry_after}s")
