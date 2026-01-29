"""
HTTPX Engine - Fast async HTTP client for lightweight scraping.
Best for APIs and sites without heavy protection.
"""

import asyncio
from typing import Optional, Dict, Any, List
import random

from loguru import logger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    NetworkError,
    TimeoutError,
    ConfigurationError,
)


class HttpxEngine(BaseScraper):
    """
    HTTPX-based async HTTP client engine.
    
    Features:
    - Native async/await support
    - HTTP/2 support
    - Connection pooling
    - Automatic retries
    - Fast and lightweight
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not HTTPX_AVAILABLE:
            raise ConfigurationError(
                "httpx not installed. Run: pip install httpx[http2]"
            )
        
        self._client: Optional[httpx.AsyncClient] = None
        self._current_html: Optional[str] = None
        self._current_url: Optional[str] = None
        self._current_response: Optional[httpx.Response] = None
    
    async def initialize(self) -> None:
        """Initialize HTTPX client."""
        # Prepare headers
        headers = dict(self.config.default_headers)
        
        if self.config.browser.user_agent:
            headers["User-Agent"] = self.config.browser.user_agent
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            headers["User-Agent"] = get_random_user_agent()
        
        # Proxy configuration
        proxy = None
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
        
        # Create client
        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.config.timeout),
            follow_redirects=True,
            http2=True,
            proxy=proxy,
        )
        
        self._initialized = True
        logger.info("HTTPX client initialized")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
        logger.info("HTTPX client closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Perform GET request."""
        try:
            response = await self._client.get(url, **kwargs)
            response.raise_for_status()
            self._current_html = response.text
            self._current_url = url
            self._current_response = response
            return response
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}", url=url)
        except httpx.HTTPStatusError as e:
            raise NetworkError(
                f"HTTP error: {e}",
                url=url,
                status_code=e.response.status_code
            )
        except Exception as e:
            raise NetworkError(f"Request failed: {e}", url=url)
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict] = None, 
        json: Optional[Dict] = None, 
        **kwargs
    ) -> Any:
        """Perform POST request."""
        try:
            response = await self._client.post(
                url, 
                data=data, 
                json=json, 
                **kwargs
            )
            response.raise_for_status()
            self._current_html = response.text
            self._current_url = url
            self._current_response = response
            return response
        except Exception as e:
            raise NetworkError(f"POST request failed: {e}", url=url)
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content."""
        if self._current_url != url or self._current_html is None:
            await self.get(url, **kwargs)
        return self._current_html
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get JSON response."""
        response = await self.get(url, **kwargs)
        return response.json()
    
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data using BeautifulSoup."""
        if not BS4_AVAILABLE:
            raise ConfigurationError(
                "beautifulsoup4 not installed. Run: pip install beautifulsoup4"
            )
        
        if not self._current_html:
            return {}
        
        soup = BeautifulSoup(self._current_html, "lxml")
        results = {}
        
        for field, selector in selectors.items():
            try:
                if selector_type == "css":
                    elements = soup.select(selector)
                else:
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
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """HTTPX doesn't support screenshots."""
        raise NotImplementedError(
            "HTTPX doesn't support screenshots. "
            "Use PlaywrightEngine or UndetectedChromeEngine instead."
        )
    
    async def execute_script(self, script: str) -> Any:
        """HTTPX doesn't support JavaScript execution."""
        raise NotImplementedError(
            "HTTPX doesn't support JavaScript execution. "
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
    
    async def download(self, url: str, path: str, **kwargs) -> str:
        """Download a file."""
        async with self._client.stream("GET", url, **kwargs) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
        return path
    
    async def head(self, url: str, **kwargs) -> httpx.Response:
        """Perform HEAD request."""
        return await self._client.head(url, **kwargs)
    
    def get_cookies(self) -> Dict[str, str]:
        """Get cookies from client."""
        return dict(self._client.cookies)
    
    def set_cookies(self, cookies: Dict[str, str]) -> None:
        """Set cookies on client."""
        self._client.cookies.update(cookies)
    
    def set_header(self, key: str, value: str) -> None:
        """Set a header on the client."""
        self._client.headers[key] = value
