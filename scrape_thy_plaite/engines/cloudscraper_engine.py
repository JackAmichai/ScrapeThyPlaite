"""
CloudScraper Engine - Cloudflare bypass using cloudscraper library.
Automatically handles Cloudflare's anti-bot protection.
"""

import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    NetworkError,
    CloudflareBlockedError,
    ConfigurationError,
)


class CloudscraperEngine(BaseScraper):
    """
    CloudScraper-based engine for bypassing Cloudflare protection.
    
    Features:
    - Automatic Cloudflare challenge solving
    - JavaScript challenge bypass
    - CAPTCHA page detection
    - Session persistence
    - Browser impersonation
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not CLOUDSCRAPER_AVAILABLE:
            raise ConfigurationError(
                "cloudscraper not installed. Run: pip install cloudscraper"
            )
        
        self._scraper: Optional[cloudscraper.CloudScraper] = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._current_html: Optional[str] = None
        self._current_url: Optional[str] = None
    
    async def initialize(self) -> None:
        """Initialize CloudScraper session."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._init_scraper)
        self._initialized = True
        logger.info("CloudScraper initialized")
    
    def _init_scraper(self) -> None:
        """Initialize the scraper (blocking)."""
        # Browser configuration for impersonation
        browser = {
            "browser": "chrome",
            "platform": "windows",
            "mobile": False,
        }
        
        self._scraper = cloudscraper.create_scraper(
            browser=browser,
            delay=10,  # Delay for JavaScript challenge
        )
        
        # Set custom headers
        self._scraper.headers.update(self.config.default_headers)
        
        # Custom user agent
        if self.config.browser.user_agent:
            self._scraper.headers["User-Agent"] = self.config.browser.user_agent
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            self._scraper.headers["User-Agent"] = get_random_user_agent()
        
        # Proxy configuration
        if self.config.proxy.enabled and self.config.proxy.proxies:
            import random
            proxy = random.choice(self.config.proxy.proxies)
            self._scraper.proxies = {
                "http": proxy,
                "https": proxy,
            }
    
    async def close(self) -> None:
        """Close the scraper session."""
        if self._scraper:
            self._scraper.close()
        self._executor.shutdown(wait=False)
        logger.info("CloudScraper closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Perform GET request with Cloudflare bypass."""
        loop = asyncio.get_event_loop()
        
        def _get():
            try:
                response = self._scraper.get(
                    url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                response.raise_for_status()
                self._current_html = response.text
                self._current_url = url
                return response
            except cloudscraper.exceptions.CloudflareChallengeError as e:
                raise CloudflareBlockedError(
                    f"Cloudflare challenge failed: {e}",
                    url=url,
                    challenge_type="javascript"
                )
            except cloudscraper.exceptions.CloudflareCaptchaError as e:
                raise CloudflareBlockedError(
                    f"Cloudflare CAPTCHA required: {e}",
                    url=url,
                    challenge_type="captcha"
                )
            except Exception as e:
                raise NetworkError(f"Request failed: {e}", url=url)
        
        return await loop.run_in_executor(self._executor, _get)
    
    async def post(self, url: str, data: Dict = None, json: Dict = None, **kwargs) -> Any:
        """Perform POST request with Cloudflare bypass."""
        loop = asyncio.get_event_loop()
        
        def _post():
            try:
                response = self._scraper.post(
                    url,
                    data=data,
                    json=json,
                    timeout=self.config.timeout,
                    **kwargs
                )
                response.raise_for_status()
                self._current_html = response.text
                self._current_url = url
                return response
            except Exception as e:
                raise NetworkError(f"POST request failed: {e}", url=url)
        
        return await loop.run_in_executor(self._executor, _post)
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content."""
        if self._current_url != url or self._current_html is None:
            await self.get(url, **kwargs)
        return self._current_html
    
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data from current page using BeautifulSoup."""
        if not BS4_AVAILABLE:
            raise ConfigurationError(
                "beautifulsoup4 not installed. Run: pip install beautifulsoup4"
            )
        
        if not self._current_html:
            return {}
        
        loop = asyncio.get_event_loop()
        
        def _extract():
            soup = BeautifulSoup(self._current_html, "lxml")
            results = {}
            
            for field, selector in selectors.items():
                try:
                    if selector_type == "css":
                        elements = soup.select(selector)
                    else:
                        # XPath not directly supported, use CSS approximation
                        elements = soup.select(selector)
                    
                    if len(elements) == 1:
                        results[field] = elements[0].get_text(strip=True)
                    elif len(elements) > 1:
                        results[field] = [el.get_text(strip=True) for el in elements]
                    else:
                        results[field] = None
                except Exception as e:
                    logger.warning(f"Extraction failed for {field}: {e}")
                    results[field] = None
            
            return results
        
        return await loop.run_in_executor(self._executor, _extract)
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """CloudScraper doesn't support screenshots."""
        raise NotImplementedError(
            "CloudScraper doesn't support screenshots. "
            "Use PlaywrightEngine or UndetectedChromeEngine instead."
        )
    
    async def execute_script(self, script: str) -> Any:
        """CloudScraper doesn't support JavaScript execution."""
        raise NotImplementedError(
            "CloudScraper doesn't support JavaScript execution. "
            "Use PlaywrightEngine or UndetectedChromeEngine instead."
        )
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        selector_type: str = "css"
    ) -> Any:
        """Check if element exists in HTML."""
        if not self._current_html:
            return None
        
        soup = BeautifulSoup(self._current_html, "lxml")
        elements = soup.select(selector) if selector_type == "css" else []
        return elements[0] if elements else None
    
    async def get_cookies(self) -> Dict[str, str]:
        """Get session cookies."""
        return dict(self._scraper.cookies)
    
    async def set_cookies(self, cookies: Dict[str, str]) -> None:
        """Set session cookies."""
        self._scraper.cookies.update(cookies)
    
    def get_cloudflare_tokens(self) -> Dict[str, str]:
        """Get Cloudflare clearance tokens for use in other tools."""
        tokens = {}
        for cookie in self._scraper.cookies:
            if "cf_" in cookie.name.lower() or "clearance" in cookie.name.lower():
                tokens[cookie.name] = cookie.value
        return tokens
