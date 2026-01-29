"""
DrissionPage Engine - Powerful browser automation that's hard to detect.
Combines browser control with packet-level operations.
"""

import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import random
import time

from loguru import logger

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    BrowserError,
    ElementNotFoundError,
    ConfigurationError,
)


class DrissionPageEngine(BaseScraper):
    """
    DrissionPage-based engine for maximum stealth.
    
    DrissionPage is a Python library that combines Selenium-like
    browser automation with requests-like packet operations,
    making it extremely difficult to detect.
    
    Features:
    - No webdriver detection
    - Real Chrome browser control
    - Packet interception
    - iframe handling
    - Shadow DOM access
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not DRISSION_AVAILABLE:
            raise ConfigurationError(
                "DrissionPage not installed. Run: pip install DrissionPage"
            )
        
        self._page: Optional[ChromiumPage] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    async def initialize(self) -> None:
        """Initialize DrissionPage browser."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._init_browser)
        self._initialized = True
        logger.info("DrissionPage browser initialized")
    
    def _init_browser(self) -> None:
        """Initialize browser (blocking)."""
        options = ChromiumOptions()
        
        # Stealth settings
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-infobars')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--no-sandbox')
        
        if self.config.browser.headless:
            options.set_argument('--headless=new')
        
        # Window size
        width, height = self.config.browser.window_size
        options.set_argument(f'--window-size={width},{height}')
        
        # User agent
        if self.config.browser.user_agent:
            options.set_argument(f'--user-agent={self.config.browser.user_agent}')
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            options.set_argument(f'--user-agent={get_random_user_agent()}')
        
        # Proxy
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            options.set_argument(f'--proxy-server={proxy}')
        
        # Additional args
        for arg in self.config.browser.args:
            options.set_argument(arg)
        
        self._page = ChromiumPage(options)
    
    async def close(self) -> None:
        """Close the browser."""
        if self._page:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self._page.quit)
        self._executor.shutdown(wait=False)
        logger.info("DrissionPage browser closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Navigate to URL."""
        loop = asyncio.get_event_loop()
        
        def _get():
            self._page.get(url)
            
            # Human-like delay
            if self.config.stealth.human_like_delays:
                time.sleep(random.uniform(
                    self.config.stealth.min_delay_ms / 1000,
                    self.config.stealth.max_delay_ms / 1000
                ))
            
            return self._page.html
        
        try:
            return await loop.run_in_executor(self._executor, _get)
        except Exception as e:
            raise BrowserError(f"Failed to navigate: {e}")
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self._page.html
        )
    
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data using selectors."""
        loop = asyncio.get_event_loop()
        
        def _extract():
            results = {}
            for field, selector in selectors.items():
                try:
                    if selector_type == "css":
                        elements = self._page.eles(f'css:{selector}')
                    else:
                        elements = self._page.eles(f'xpath:{selector}')
                    
                    if len(elements) == 1:
                        results[field] = elements[0].text
                    elif len(elements) > 1:
                        results[field] = [el.text for el in elements]
                    else:
                        results[field] = None
                except Exception:
                    results[field] = None
            return results
        
        return await loop.run_in_executor(self._executor, _extract)
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """Take screenshot."""
        loop = asyncio.get_event_loop()
        
        def _screenshot():
            if path:
                self._page.get_screenshot(path=path)
                with open(path, 'rb') as f:
                    return f.read()
            return self._page.get_screenshot(as_bytes='png')
        
        return await loop.run_in_executor(self._executor, _screenshot)
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self._page.run_js(script)
        )
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        selector_type: str = "css"
    ) -> Any:
        """Wait for element."""
        loop = asyncio.get_event_loop()
        timeout = timeout or self.config.timeout
        
        def _wait():
            prefix = 'css:' if selector_type == 'css' else 'xpath:'
            element = self._page.ele(f'{prefix}{selector}', timeout=timeout)
            if not element:
                raise ElementNotFoundError(f"Element not found: {selector}", selector=selector)
            return element
        
        return await loop.run_in_executor(self._executor, _wait)
    
    async def click(self, selector: str, selector_type: str = "css") -> None:
        """Click element with human-like behavior."""
        loop = asyncio.get_event_loop()
        
        def _click():
            prefix = 'css:' if selector_type == 'css' else 'xpath:'
            element = self._page.ele(f'{prefix}{selector}')
            
            if self.config.stealth.human_like_delays:
                # Move mouse naturally
                element.hover()
                time.sleep(random.uniform(0.1, 0.3))
            
            element.click()
        
        await loop.run_in_executor(self._executor, _click)
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        selector_type: str = "css",
        clear: bool = True
    ) -> None:
        """Type text with human-like delays."""
        loop = asyncio.get_event_loop()
        
        def _type():
            prefix = 'css:' if selector_type == 'css' else 'xpath:'
            element = self._page.ele(f'{prefix}{selector}')
            
            if clear:
                element.clear()
            
            if self.config.stealth.human_like_delays:
                for char in text:
                    element.input(char)
                    time.sleep(random.uniform(0.05, 0.15))
            else:
                element.input(text)
        
        await loop.run_in_executor(self._executor, _type)
    
    async def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            lambda: self._page.scroll.to_bottom()
        )
    
    async def handle_alert(self, accept: bool = True) -> str:
        """Handle JavaScript alert."""
        loop = asyncio.get_event_loop()
        
        def _handle():
            alert = self._page.handle_alert(accept=accept)
            return alert
        
        return await loop.run_in_executor(self._executor, _handle)
