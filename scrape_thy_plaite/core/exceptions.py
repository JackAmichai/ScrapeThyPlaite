"""
Custom exceptions for ScrapeThyPlaite.
"""

from typing import Optional, Any


class ScraperException(Exception):
    """Base exception for all scraper-related errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(ScraperException):
    """Raised when there's a configuration error."""
    pass


class NetworkError(ScraperException):
    """Raised for network-related errors."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        self.url = url
        self.status_code = status_code
        super().__init__(message, {"url": url, "status_code": status_code, **kwargs})


class TimeoutError(NetworkError):
    """Raised when a request times out."""
    pass


class ConnectionError(NetworkError):
    """Raised when connection fails."""
    pass


class ProxyError(NetworkError):
    """Raised for proxy-related errors."""
    
    def __init__(self, message: str, proxy: Optional[str] = None, **kwargs):
        self.proxy = proxy
        super().__init__(message, proxy=proxy, **kwargs)


class CaptchaError(ScraperException):
    """Base exception for CAPTCHA-related errors."""
    pass


class CaptchaUnsolvableError(CaptchaError):
    """Raised when CAPTCHA cannot be solved."""
    pass


class CaptchaTimeoutError(CaptchaError):
    """Raised when CAPTCHA solving times out."""
    pass


class CaptchaProviderError(CaptchaError):
    """Raised for CAPTCHA provider API errors."""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.provider = provider
        self.error_code = error_code
        super().__init__(message, {"provider": provider, "error_code": error_code})


class CaptchaInsufficientFundsError(CaptchaProviderError):
    """Raised when CAPTCHA provider account has insufficient funds."""
    pass


class BlockedError(ScraperException):
    """Raised when scraper is blocked by the target site."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        block_type: Optional[str] = None,
        **kwargs
    ):
        self.url = url
        self.block_type = block_type
        super().__init__(message, {"url": url, "block_type": block_type, **kwargs})


class CloudflareBlockedError(BlockedError):
    """Raised when blocked by Cloudflare."""
    
    def __init__(self, message: str, challenge_type: Optional[str] = None, **kwargs):
        self.challenge_type = challenge_type
        super().__init__(message, block_type="cloudflare", **kwargs)


class RateLimitError(BlockedError):
    """Raised when rate limited by target site."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, block_type="rate_limit", **kwargs)


class BotDetectedError(BlockedError):
    """Raised when bot detection is triggered."""
    pass


class ExtractionError(ScraperException):
    """Raised when data extraction fails."""
    
    def __init__(
        self, 
        message: str, 
        selector: Optional[str] = None,
        element: Optional[str] = None,
        **kwargs
    ):
        self.selector = selector
        self.element = element
        super().__init__(message, {"selector": selector, "element": element, **kwargs})


class ElementNotFoundError(ExtractionError):
    """Raised when target element is not found."""
    pass


class ParsingError(ExtractionError):
    """Raised when parsing content fails."""
    pass


class ValidationError(ScraperException):
    """Raised when data validation fails."""
    pass


class StorageError(ScraperException):
    """Raised for storage/export related errors."""
    pass


class BrowserError(ScraperException):
    """Raised for browser-related errors."""
    pass


class BrowserCrashedError(BrowserError):
    """Raised when browser crashes."""
    pass


class PageLoadError(BrowserError):
    """Raised when page fails to load."""
    pass


class RobotsDisallowedError(ScraperException):
    """Raised when URL is disallowed by robots.txt."""
    
    def __init__(self, message: str, url: str, **kwargs):
        self.url = url
        super().__init__(message, {"url": url, **kwargs})


class RetryExhaustedError(ScraperException):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int, last_error: Optional[Exception] = None):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message, {"attempts": attempts, "last_error": str(last_error)})
