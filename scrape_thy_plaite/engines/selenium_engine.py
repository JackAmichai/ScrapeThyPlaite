"""
Standard Selenium Engine - Traditional browser automation.
"""

import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import random
import time

from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    BrowserError,
    ElementNotFoundError,
    ConfigurationError,
)


class SeleniumEngine(BaseScraper):
    """
    Standard Selenium WebDriver engine.
    
    Features:
    - Full browser automation
    - WebDriver manager for automatic driver setup
    - Support for Chrome, Firefox, Edge
    - Configurable options
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not SELENIUM_AVAILABLE:
            raise ConfigurationError(
                "selenium not installed. Run: pip install selenium webdriver-manager"
            )
        
        self.driver: Optional[webdriver.Chrome] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    async def initialize(self) -> None:
        """Initialize Selenium WebDriver."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._init_driver)
        self._initialized = True
        logger.info("Selenium WebDriver initialized")
    
    def _init_driver(self) -> None:
        """Initialize the driver (blocking)."""
        options = Options()
        
        if self.config.browser.headless:
            options.add_argument("--headless=new")
        
        width, height = self.config.browser.window_size
        options.add_argument(f"--window-size={width},{height}")
        
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        
        if self.config.browser.user_agent:
            options.add_argument(f"--user-agent={self.config.browser.user_agent}")
        
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            options.add_argument(f"--proxy-server={proxy}")
        
        for arg in self.config.browser.args:
            options.add_argument(arg)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.driver.implicitly_wait(self.config.timeout)
    
    async def close(self) -> None:
        """Close the browser."""
        if self.driver:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self.driver.quit)
            self.driver = None
        self._executor.shutdown(wait=False)
        logger.info("Selenium WebDriver closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Navigate to URL."""
        loop = asyncio.get_event_loop()
        
        def _get():
            self.driver.get(url)
            return self.driver.page_source
        
        try:
            return await loop.run_in_executor(self._executor, _get)
        except Exception as e:
            raise BrowserError(f"Failed to navigate to {url}: {e}")
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            lambda: self.driver.page_source
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
            by = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
            
            for field, selector in selectors.items():
                try:
                    elements = self.driver.find_elements(by, selector)
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
                self.driver.save_screenshot(path)
                with open(path, "rb") as f:
                    return f.read()
            return self.driver.get_screenshot_as_png()
        
        return await loop.run_in_executor(self._executor, _screenshot)
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.driver.execute_script(script)
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
            by = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        
        try:
            return await loop.run_in_executor(self._executor, _wait)
        except Exception:
            raise ElementNotFoundError(
                f"Element not found: {selector}",
                selector=selector
            )
