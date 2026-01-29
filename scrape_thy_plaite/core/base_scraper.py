"""
Base Scraper - Core scraping functionality for ScrapeThyPlaite.
Provides a unified interface for all scraping engines.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Union, AsyncGenerator
from urllib.parse import urlparse, urljoin
from datetime import datetime
import hashlib
import json

from loguru import logger
from pydantic import BaseModel

from scrape_thy_plaite.core.config import ScraperConfig, EngineType
from scrape_thy_plaite.core.exceptions import (
    ScraperException,
    ConfigurationError,
    RobotsDisallowedError,
    ElementNotFoundError,
    RetryExhaustedError,
)
from scrape_thy_plaite.utils.retry import RetryHandler
from scrape_thy_plaite.utils.rate_limiter import RateLimiter
from scrape_thy_plaite.stealth.fingerprint import FingerprintGenerator


class ScrapedData(BaseModel):
    """Model for scraped data with metadata."""
    url: str
    timestamp: datetime
    data: Dict[str, Any]
    html: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    screenshot: Optional[bytes] = None
    fingerprint: Optional[str] = None
    
    def to_hash(self) -> str:
        """Generate a unique hash for this data."""
        content = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class BaseScraper(ABC):
    """
    Abstract base class for all scraping engines.
    
    All engine implementations must inherit from this class
    and implement the abstract methods.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self._setup_logging()
        self._initialized = False
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        
        # Initialize components based on config
        if self.config.retry.enabled:
            self.retry_handler = RetryHandler(self.config.retry)
        else:
            self.retry_handler = None
            
        if self.config.rate_limit.enabled:
            self.rate_limiter = RateLimiter(self.config.rate_limit)
        else:
            self.rate_limiter = None
            
        if self.config.stealth.enabled:
            self.fingerprint_generator = FingerprintGenerator(self.config.stealth)
        else:
            self.fingerprint_generator = None
    
    def _setup_logging(self):
        """Configure logging based on config."""
        logger.remove()
        logger.add(
            lambda msg: print(msg),
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the scraping engine (browser, session, etc.)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass
    
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Any:
        """Perform a GET request to the URL."""
        pass
    
    @abstractmethod
    async def get_html(self, url: str, **kwargs) -> str:
        """Get the HTML content of a page."""
        pass
    
    @abstractmethod
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data using selectors from current page."""
        pass
    
    @abstractmethod
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot of the current page."""
        pass
    
    @abstractmethod
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the current page."""
        pass
    
    @abstractmethod
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        selector_type: str = "css"
    ) -> Any:
        """Wait for an element to appear on the page."""
        pass
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _should_respect_robots(self, url: str) -> bool:
        """Check if we should respect robots.txt for this URL."""
        if not self.config.respect_robots_txt:
            return True
        # Implement robots.txt checking here
        return True
    
    async def _apply_rate_limit(self, url: str) -> None:
        """Apply rate limiting if enabled."""
        if self.rate_limiter:
            domain = urlparse(url).netloc
            await self.rate_limiter.acquire(domain)
    
    def _get_fingerprint(self) -> Optional[Dict[str, Any]]:
        """Generate a browser fingerprint if stealth is enabled."""
        if self.fingerprint_generator:
            return self.fingerprint_generator.generate()
        return None


class Scraper:
    """
    Main Scraper class - High-level interface for web scraping.
    
    This class automatically selects and configures the appropriate
    scraping engine based on configuration.
    
    Example:
        async with Scraper(config) as scraper:
            data = await scraper.scrape(
                url="https://example.com",
                selectors={"title": "h1", "content": ".article"}
            )
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self._engine: Optional[BaseScraper] = None
        self._robots_cache: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize the scraper with the configured engine."""
        self._engine = await self._create_engine()
        await self._engine.initialize()
        logger.info(f"Scraper initialized with engine: {self.config.engine}")
    
    async def _create_engine(self) -> BaseScraper:
        """Create the appropriate scraping engine based on config."""
        engine_type = self.config.engine
        
        if engine_type == EngineType.SELENIUM:
            from scrape_thy_plaite.engines.selenium_engine import SeleniumEngine
            return SeleniumEngine(self.config)
        
        elif engine_type == EngineType.PLAYWRIGHT:
            from scrape_thy_plaite.engines.playwright_engine import PlaywrightEngine
            return PlaywrightEngine(self.config)
        
        elif engine_type == EngineType.UNDETECTED_CHROME:
            from scrape_thy_plaite.engines.undetected_chrome import UndetectedChromeEngine
            return UndetectedChromeEngine(self.config)
        
        elif engine_type == EngineType.CLOUDSCRAPER:
            from scrape_thy_plaite.engines.cloudscraper_engine import CloudscraperEngine
            return CloudscraperEngine(self.config)
        
        elif engine_type == EngineType.HTTPX:
            from scrape_thy_plaite.engines.httpx_engine import HttpxEngine
            return HttpxEngine(self.config)
        
        else:
            raise ConfigurationError(f"Unknown engine type: {engine_type}")
    
    async def close(self) -> None:
        """Close the scraper and release resources."""
        if self._engine:
            await self._engine.close()
            logger.info("Scraper closed")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def scrape(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        wait_for: Optional[str] = None,
        extract_html: bool = False,
        take_screenshot: bool = False,
        **kwargs
    ) -> ScrapedData:
        """
        Scrape data from a URL.
        
        Args:
            url: The URL to scrape
            selectors: Dict mapping field names to CSS/XPath selectors
            wait_for: Selector to wait for before extraction
            extract_html: Whether to include raw HTML in response
            take_screenshot: Whether to take a screenshot
            **kwargs: Additional arguments passed to the engine
            
        Returns:
            ScrapedData object with extracted data and metadata
        """
        if not self._engine:
            raise ConfigurationError("Scraper not initialized. Use 'async with' or call initialize()")
        
        # Check robots.txt
        if self.config.respect_robots_txt:
            if not await self._check_robots(url):
                raise RobotsDisallowedError(
                    f"URL disallowed by robots.txt: {url}",
                    url=url
                )
        
        # Apply rate limiting
        await self._engine._apply_rate_limit(url)
        
        # Navigate to URL
        logger.info(f"Scraping: {url}")
        response = await self._engine.get(url, **kwargs)
        
        # Wait for element if specified
        if wait_for:
            await self._engine.wait_for_element(wait_for, timeout=self.config.timeout)
        
        # Extract data
        data = {}
        if selectors:
            data = await self._engine.extract(selectors)
        
        # Get HTML if requested
        html = None
        if extract_html:
            html = await self._engine.get_html(url)
        
        # Take screenshot if requested
        screenshot = None
        if take_screenshot:
            screenshot = await self._engine.screenshot()
        
        return ScrapedData(
            url=url,
            timestamp=datetime.now(),
            data=data,
            html=html,
            screenshot=screenshot,
            fingerprint=self._engine.session_id,
        )
    
    async def scrape_multiple(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None,
        concurrency: int = 5,
        **kwargs
    ) -> AsyncGenerator[ScrapedData, None]:
        """
        Scrape multiple URLs with controlled concurrency.
        
        Args:
            urls: List of URLs to scrape
            selectors: Selectors to use for all URLs
            concurrency: Maximum concurrent requests
            **kwargs: Additional arguments
            
        Yields:
            ScrapedData objects as they complete
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str) -> ScrapedData:
            async with semaphore:
                return await self.scrape(url, selectors=selectors, **kwargs)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                yield result
            except Exception as e:
                logger.error(f"Error scraping: {e}")
    
    async def _check_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        if robots_url not in self._robots_cache:
            # Fetch and parse robots.txt
            try:
                # Simple implementation - should use robotparser
                self._robots_cache[robots_url] = True
            except Exception:
                self._robots_cache[robots_url] = True
        
        return self._robots_cache.get(robots_url, True)
    
    async def solve_captcha(
        self,
        site_key: str,
        captcha_type: str = "recaptcha_v2",
        **kwargs
    ) -> str:
        """
        Solve a CAPTCHA on the current page.
        
        Args:
            site_key: The CAPTCHA site key
            captcha_type: Type of CAPTCHA (recaptcha_v2, recaptcha_v3, hcaptcha)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            CAPTCHA solution token
        """
        from scrape_thy_plaite.captcha import CaptchaSolver
        
        solver = CaptchaSolver(self.config.captcha)
        return await solver.solve(
            site_key=site_key,
            captcha_type=captcha_type,
            page_url=kwargs.get("page_url", ""),
            **kwargs
        )
