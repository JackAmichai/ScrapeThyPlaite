"""
Undetected Chrome Engine - Selenium-based engine with anti-detection.
Uses undetected-chromedriver to bypass bot detection.
"""

import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import random
import time

from loguru import logger

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        WebDriverException,
    )
except ImportError:
    uc = None

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    BrowserError,
    ElementNotFoundError,
    TimeoutError,
    ConfigurationError,
)
from scrape_thy_plaite.stealth.evasion import apply_stealth_scripts


class UndetectedChromeEngine(BaseScraper):
    """
    Undetected Chrome Engine using undetected-chromedriver.
    
    This engine is specifically designed to bypass bot detection systems
    including Cloudflare, DataDome, PerimeterX, and others.
    
    Features:
    - Automatic Chrome driver management
    - Anti-detection patches applied automatically
    - Human-like behavior simulation
    - Fingerprint randomization
    - Stealth JavaScript injection
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if uc is None:
            raise ConfigurationError(
                "undetected-chromedriver not installed. "
                "Run: pip install undetected-chromedriver"
            )
        
        self.driver: Optional[uc.Chrome] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    async def initialize(self) -> None:
        """Initialize the undetected Chrome browser."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._init_driver)
        self._initialized = True
        logger.info("Undetected Chrome browser initialized")
    
    def _init_driver(self) -> None:
        """Initialize the Chrome driver (blocking)."""
        options = uc.ChromeOptions()
        
        # Apply configuration
        if self.config.browser.headless:
            options.add_argument("--headless=new")
        
        # Window size
        width, height = self.config.browser.window_size
        options.add_argument(f"--window-size={width},{height}")
        
        # Additional stealth options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        
        # Language/locale
        if self.config.browser.locale:
            options.add_argument(f"--lang={self.config.browser.locale}")
        
        # Disable images if configured
        if self.config.browser.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        # Custom user agent
        if self.config.browser.user_agent:
            options.add_argument(f"--user-agent={self.config.browser.user_agent}")
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            ua = get_random_user_agent()
            options.add_argument(f"--user-agent={ua}")
        
        # Add custom arguments
        for arg in self.config.browser.args:
            options.add_argument(arg)
        
        # Proxy configuration
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            options.add_argument(f"--proxy-server={proxy}")
        
        # Initialize undetected Chrome
        self.driver = uc.Chrome(
            options=options,
            version_main=None,  # Auto-detect Chrome version
            use_subprocess=True,
        )
        
        # Set timeouts
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.driver.implicitly_wait(self.config.timeout)
        
        # Apply additional stealth measures
        if self.config.stealth.enabled:
            self._apply_stealth()
    
    def _apply_stealth(self) -> None:
        """Apply additional stealth measures to the browser."""
        stealth_scripts = apply_stealth_scripts(self.config.stealth)
        
        # Execute stealth scripts
        for script in stealth_scripts:
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": script
                })
            except Exception as e:
                logger.warning(f"Failed to apply stealth script: {e}")
    
    async def close(self) -> None:
        """Close the browser and clean up."""
        if self.driver:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self.driver.quit)
            self.driver = None
        self._executor.shutdown(wait=False)
        logger.info("Undetected Chrome browser closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Navigate to a URL."""
        loop = asyncio.get_event_loop()
        
        def _get():
            self.driver.get(url)
            # Add human-like delay
            if self.config.stealth.human_like_delays:
                time.sleep(random.uniform(
                    self.config.stealth.min_delay_ms / 1000,
                    self.config.stealth.max_delay_ms / 1000
                ))
            return self.driver.page_source
        
        try:
            return await loop.run_in_executor(self._executor, _get)
        except WebDriverException as e:
            raise BrowserError(f"Failed to navigate to {url}: {e}")
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content of current page."""
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
        """Extract data using CSS or XPath selectors."""
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
                except NoSuchElementException:
                    results[field] = None
                    logger.warning(f"Element not found: {selector}")
            
            return results
        
        return await loop.run_in_executor(self._executor, _extract)
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot of the current page."""
        loop = asyncio.get_event_loop()
        
        def _screenshot():
            if path:
                self.driver.save_screenshot(path)
                with open(path, "rb") as f:
                    return f.read()
            return self.driver.get_screenshot_as_png()
        
        return await loop.run_in_executor(self._executor, _screenshot)
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
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
        """Wait for an element to appear."""
        loop = asyncio.get_event_loop()
        timeout = timeout or self.config.timeout
        
        def _wait():
            by = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
            except TimeoutException:
                raise ElementNotFoundError(
                    f"Element not found within {timeout}s",
                    selector=selector
                )
        
        return await loop.run_in_executor(self._executor, _wait)
    
    async def click(self, selector: str, selector_type: str = "css") -> None:
        """Click an element with human-like behavior."""
        loop = asyncio.get_event_loop()
        
        def _click():
            by = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
            element = self.driver.find_element(by, selector)
            
            if self.config.stealth.human_like_delays:
                # Move to element first
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.pause(random.uniform(0.1, 0.3))
                actions.click()
                actions.perform()
            else:
                element.click()
        
        await loop.run_in_executor(self._executor, _click)
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        selector_type: str = "css",
        human_like: bool = True
    ) -> None:
        """Type text into an input field with optional human-like behavior."""
        loop = asyncio.get_event_loop()
        
        def _type():
            by = By.CSS_SELECTOR if selector_type == "css" else By.XPATH
            element = self.driver.find_element(by, selector)
            element.clear()
            
            if human_like and self.config.stealth.human_like_delays:
                # Type character by character with random delays
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            else:
                element.send_keys(text)
        
        await loop.run_in_executor(self._executor, _type)
    
    async def scroll_to_bottom(self, pause: float = 0.5) -> None:
        """Scroll to the bottom of the page."""
        loop = asyncio.get_event_loop()
        
        def _scroll():
            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            
            while True:
                # Scroll down
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(pause)
                
                # Calculate new scroll height
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                
                if new_height == last_height:
                    break
                last_height = new_height
        
        await loop.run_in_executor(self._executor, _scroll)
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies from the browser."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.driver.get_cookies
        )
    
    async def add_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Add cookies to the browser."""
        loop = asyncio.get_event_loop()
        
        def _add_cookies():
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        
        await loop.run_in_executor(self._executor, _add_cookies)
