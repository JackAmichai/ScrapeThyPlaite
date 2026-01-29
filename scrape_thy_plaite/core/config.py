"""
Core configuration module for ScrapeThyPlaite.
Defines all configuration options and settings.
"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class EngineType(str, Enum):
    """Supported scraping engine types."""
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    UNDETECTED_CHROME = "undetected_chrome"
    CLOUDSCRAPER = "cloudscraper"
    HTTPX = "httpx"
    REQUESTS = "requests"


class CaptchaProvider(str, Enum):
    """Supported CAPTCHA solving providers."""
    TWO_CAPTCHA = "2captcha"
    ANTICAPTCHA = "anticaptcha"
    CAPMONSTER = "capmonster"
    NONE = "none"


class ProxyRotationStrategy(str, Enum):
    """Proxy rotation strategies."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_USED = "least_used"
    STICKY = "sticky"


class BrowserConfig(BaseModel):
    """Browser-specific configuration."""
    headless: bool = True
    window_size: tuple[int, int] = (1920, 1080)
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None
    disable_images: bool = False
    disable_javascript: bool = False
    download_path: Optional[str] = None
    extensions: List[str] = Field(default_factory=list)
    args: List[str] = Field(default_factory=list)


class StealthConfig(BaseModel):
    """Stealth and anti-detection configuration."""
    enabled: bool = True
    randomize_fingerprint: bool = True
    randomize_viewport: bool = True
    randomize_user_agent: bool = True
    mask_webdriver: bool = True
    mask_automation: bool = True
    spoof_plugins: bool = True
    spoof_languages: bool = True
    spoof_webgl: bool = True
    spoof_audio_context: bool = True
    human_like_delays: bool = True
    min_delay_ms: int = 100
    max_delay_ms: int = 500


class ProxyConfig(BaseModel):
    """Proxy configuration."""
    enabled: bool = False
    proxies: List[str] = Field(default_factory=list)
    rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.ROUND_ROBIN
    health_check: bool = True
    health_check_url: str = "https://httpbin.org/ip"
    max_failures: int = 3
    sticky_session_duration: int = 300  # seconds


class CaptchaConfig(BaseModel):
    """CAPTCHA solving configuration."""
    enabled: bool = False
    provider: CaptchaProvider = CaptchaProvider.NONE
    api_key: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    soft_id: Optional[str] = None


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_second: float = 1.0
    requests_per_minute: Optional[int] = None
    burst_size: int = 5
    domain_specific: Dict[str, float] = Field(default_factory=dict)


class RetryConfig(BaseModel):
    """Retry configuration."""
    enabled: bool = True
    max_retries: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    retry_on_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
    retry_on_exceptions: List[str] = Field(
        default_factory=lambda: ["ConnectionError", "Timeout", "SSLError"]
    )


class ExportConfig(BaseModel):
    """Data export configuration."""
    format: Literal["json", "csv", "parquet", "sqlite"] = "json"
    output_path: str = "./output"
    filename_template: str = "{domain}_{timestamp}"
    compress: bool = False
    pretty_print: bool = True


class ScraperConfig(BaseModel):
    """
    Main configuration class for ScrapeThyPlaite scraper.
    
    Example:
        config = ScraperConfig(
            engine=EngineType.UNDETECTED_CHROME,
            browser=BrowserConfig(headless=False),
            stealth=StealthConfig(enabled=True),
            captcha=CaptchaConfig(
                enabled=True,
                provider=CaptchaProvider.TWO_CAPTCHA,
                api_key="your_api_key"
            )
        )
    """
    
    # Core settings
    engine: EngineType = EngineType.UNDETECTED_CHROME
    timeout: int = 30
    page_load_timeout: int = 60
    
    # Ethical scraping
    respect_robots_txt: bool = True
    respect_meta_robots: bool = True
    honor_retry_after: bool = True
    
    # Sub-configurations
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    stealth: StealthConfig = Field(default_factory=StealthConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    captcha: CaptchaConfig = Field(default_factory=CaptchaConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    
    # Headers
    default_headers: Dict[str, str] = Field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    
    # Cookies
    cookies: Dict[str, str] = Field(default_factory=dict)
    persist_cookies: bool = True
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_requests: bool = False
    log_responses: bool = False
    
    @field_validator("timeout", "page_load_timeout")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    class Config:
        use_enum_values = True


# Preset configurations for common use cases
class ConfigPresets:
    """Pre-configured settings for common scraping scenarios."""
    
    @staticmethod
    def stealth_mode() -> ScraperConfig:
        """Maximum stealth configuration for heavily protected sites."""
        return ScraperConfig(
            engine=EngineType.UNDETECTED_CHROME,
            stealth=StealthConfig(
                enabled=True,
                randomize_fingerprint=True,
                randomize_viewport=True,
                randomize_user_agent=True,
                mask_webdriver=True,
                human_like_delays=True,
                min_delay_ms=500,
                max_delay_ms=2000,
            ),
            rate_limit=RateLimitConfig(
                enabled=True,
                requests_per_second=0.5,
            ),
        )
    
    @staticmethod
    def fast_mode() -> ScraperConfig:
        """Fast scraping for lightweight, unprotected sites."""
        return ScraperConfig(
            engine=EngineType.HTTPX,
            browser=BrowserConfig(headless=True),
            stealth=StealthConfig(enabled=False),
            rate_limit=RateLimitConfig(
                enabled=True,
                requests_per_second=10.0,
            ),
        )
    
    @staticmethod
    def cloudflare_mode() -> ScraperConfig:
        """Configuration optimized for Cloudflare-protected sites."""
        return ScraperConfig(
            engine=EngineType.CLOUDSCRAPER,
            stealth=StealthConfig(enabled=True),
            retry=RetryConfig(
                enabled=True,
                max_retries=5,
                retry_on_status_codes=[403, 429, 503],
            ),
        )
    
    @staticmethod
    def javascript_heavy() -> ScraperConfig:
        """Configuration for JavaScript-heavy SPAs."""
        return ScraperConfig(
            engine=EngineType.PLAYWRIGHT,
            browser=BrowserConfig(
                headless=True,
                disable_javascript=False,
            ),
            page_load_timeout=120,
        )
