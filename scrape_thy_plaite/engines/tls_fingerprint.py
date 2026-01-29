"""
TLS Fingerprint Engine - Advanced TLS/JA3 fingerprint spoofing.
Uses curl_cffi to impersonate real browsers at the TLS level.
"""

import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import random
import json

from loguru import logger

try:
    from curl_cffi import requests as curl_requests
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    NetworkError,
    ConfigurationError,
    BlockedError,
)


# Browser impersonation options for curl_cffi
BROWSER_IMPERSONATIONS = [
    "chrome110",
    "chrome107",
    "chrome104",
    "chrome101",
    "chrome100",
    "chrome99",
    "edge101",
    "edge99",
    "safari15_5",
    "safari15_3",
]


class TLSFingerprintEngine(BaseScraper):
    """
    TLS Fingerprint Spoofing Engine using curl_cffi.
    
    This engine impersonates real browsers at the TLS/SSL level,
    making it nearly impossible to detect as a bot based on
    TLS fingerprinting (JA3/JA3S).
    
    Features:
    - Real browser TLS fingerprints (Chrome, Edge, Safari)
    - HTTP/2 support
    - Automatic cookie handling
    - Session persistence
    - Bypasses advanced bot detection (Akamai, PerimeterX, DataDome)
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not CURL_CFFI_AVAILABLE:
            raise ConfigurationError(
                "curl_cffi not installed. Run: pip install curl_cffi"
            )
        
        self._session: Optional[AsyncSession] = None
        self._current_html: Optional[str] = None
        self._current_url: Optional[str] = None
        self._impersonate: str = "chrome110"
    
    async def initialize(self) -> None:
        """Initialize the TLS session."""
        # Select browser to impersonate
        if self.config.stealth.randomize_fingerprint:
            self._impersonate = random.choice(BROWSER_IMPERSONATIONS)
        
        # Build headers
        headers = dict(self.config.default_headers)
        if self.config.browser.user_agent:
            headers["User-Agent"] = self.config.browser.user_agent
        
        # Create async session with browser impersonation
        self._session = AsyncSession(
            impersonate=self._impersonate,
            headers=headers,
            timeout=self.config.timeout,
        )
        
        # Configure proxy if enabled
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            self._session.proxies = {"http": proxy, "https": proxy}
        
        self._initialized = True
        logger.info(f"TLS Fingerprint Engine initialized (impersonating {self._impersonate})")
    
    async def close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
        logger.info("TLS Fingerprint Engine closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Perform GET request with TLS fingerprint spoofing."""
        try:
            response = await self._session.get(url, **kwargs)
            self._current_html = response.text
            self._current_url = url
            
            # Check for blocks
            if response.status_code == 403:
                raise BlockedError(f"Access forbidden: {url}", url=url)
            elif response.status_code == 429:
                raise BlockedError(f"Rate limited: {url}", url=url, block_type="rate_limit")
            
            response.raise_for_status()
            return response
            
        except Exception as e:
            if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                raise BlockedError(f"Blocked: {e}", url=url)
            raise NetworkError(f"Request failed: {e}", url=url)
    
    async def post(self, url: str, data: Dict = None, json_data: Dict = None, **kwargs) -> Any:
        """Perform POST request with TLS fingerprint spoofing."""
        try:
            response = await self._session.post(
                url, 
                data=data, 
                json=json_data,
                **kwargs
            )
            self._current_html = response.text
            self._current_url = url
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
            raise ConfigurationError("beautifulsoup4 not installed")
        
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
        """Not supported - use browser engine."""
        raise NotImplementedError("TLS engine doesn't support screenshots")
    
    async def execute_script(self, script: str) -> Any:
        """Not supported - use browser engine."""
        raise NotImplementedError("TLS engine doesn't support JavaScript")
    
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
    
    def get_cookies(self) -> Dict[str, str]:
        """Get session cookies."""
        return dict(self._session.cookies)
    
    def set_cookies(self, cookies: Dict[str, str]) -> None:
        """Set session cookies."""
        for name, value in cookies.items():
            self._session.cookies.set(name, value)
    
    def rotate_impersonation(self) -> str:
        """Rotate to a different browser impersonation."""
        self._impersonate = random.choice(BROWSER_IMPERSONATIONS)
        logger.info(f"Rotated to impersonate: {self._impersonate}")
        return self._impersonate
