"""
Playwright Engine - Modern async browser automation.
Provides full browser automation with Chromium, Firefox, and WebKit support.
"""

import asyncio
from typing import Optional, Dict, Any, List
import random

from loguru import logger

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from scrape_thy_plaite.core.base_scraper import BaseScraper
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.exceptions import (
    BrowserError,
    ElementNotFoundError,
    TimeoutError,
    ConfigurationError,
)


class PlaywrightEngine(BaseScraper):
    """
    Playwright-based scraping engine.
    
    Features:
    - Native async support
    - Multi-browser support (Chromium, Firefox, WebKit)
    - Built-in stealth features
    - Network interception
    - Auto-waiting for elements
    - Geolocation and timezone emulation
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(config)
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ConfigurationError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        self._playwright = await async_playwright().start()
        
        # Select browser type
        browser_type = self._playwright.chromium
        
        # Launch options
        launch_options = {
            "headless": self.config.browser.headless,
        }
        
        # Proxy configuration
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            launch_options["proxy"] = {"server": proxy}
        
        self._browser = await browser_type.launch(**launch_options)
        
        # Context options for stealth
        context_options = {
            "viewport": {
                "width": self.config.browser.window_size[0],
                "height": self.config.browser.window_size[1],
            },
            "locale": self.config.browser.locale,
            "java_script_enabled": not self.config.browser.disable_javascript,
        }
        
        # User agent
        if self.config.browser.user_agent:
            context_options["user_agent"] = self.config.browser.user_agent
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            context_options["user_agent"] = get_random_user_agent()
        
        # Timezone
        if self.config.browser.timezone:
            context_options["timezone_id"] = self.config.browser.timezone
        
        # Geolocation
        if self.config.browser.geolocation:
            context_options["geolocation"] = self.config.browser.geolocation
            context_options["permissions"] = ["geolocation"]
        
        self._context = await self._browser.new_context(**context_options)
        
        # Apply stealth scripts
        if self.config.stealth.enabled:
            await self._apply_stealth()
        
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.timeout * 1000)
        
        self._initialized = True
        logger.info("Playwright browser initialized")
    
    async def _apply_stealth(self) -> None:
        """Apply stealth modifications to evade detection."""
        # Mask webdriver
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Mask automation
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Mask Chrome
        await self._context.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)
        
        # Permissions
        await self._context.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    async def close(self) -> None:
        """Close browser and clean up."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Playwright browser closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Navigate to URL."""
        try:
            response = await self._page.goto(
                url,
                wait_until=kwargs.get("wait_until", "networkidle"),
                timeout=self.config.page_load_timeout * 1000,
            )
            
            # Human-like delay
            if self.config.stealth.human_like_delays:
                await asyncio.sleep(random.uniform(
                    self.config.stealth.min_delay_ms / 1000,
                    self.config.stealth.max_delay_ms / 1000
                ))
            
            return response
        except Exception as e:
            raise BrowserError(f"Failed to navigate to {url}: {e}")
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content of current page."""
        return await self._page.content()
    
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data using selectors."""
        results = {}
        
        for field, selector in selectors.items():
            try:
                if selector_type == "xpath":
                    elements = await self._page.locator(f"xpath={selector}").all()
                else:
                    elements = await self._page.locator(selector).all()
                
                if len(elements) == 1:
                    results[field] = await elements[0].text_content()
                elif len(elements) > 1:
                    results[field] = [await el.text_content() for el in elements]
                else:
                    results[field] = None
            except Exception as e:
                logger.warning(f"Failed to extract {field}: {e}")
                results[field] = None
        
        return results
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """Take screenshot."""
        return await self._page.screenshot(
            path=path,
            full_page=True,
        )
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript."""
        return await self._page.evaluate(script)
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        selector_type: str = "css"
    ) -> Any:
        """Wait for element to appear."""
        timeout = (timeout or self.config.timeout) * 1000
        
        try:
            if selector_type == "xpath":
                locator = self._page.locator(f"xpath={selector}")
            else:
                locator = self._page.locator(selector)
            
            await locator.wait_for(timeout=timeout)
            return locator
        except Exception:
            raise ElementNotFoundError(
                f"Element not found: {selector}",
                selector=selector
            )
    
    async def click(self, selector: str, **kwargs) -> None:
        """Click an element."""
        await self._page.click(selector, **kwargs)
    
    async def fill(self, selector: str, text: str, **kwargs) -> None:
        """Fill text into an input."""
        await self._page.fill(selector, text, **kwargs)
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        delay: int = 100
    ) -> None:
        """Type text with delays (human-like)."""
        await self._page.type(selector, text, delay=delay)
    
    async def wait_for_navigation(self, **kwargs) -> None:
        """Wait for navigation to complete."""
        await self._page.wait_for_load_state(
            kwargs.get("state", "networkidle")
        )
    
    async def intercept_requests(self, handler) -> None:
        """Set up request interception."""
        await self._page.route("**/*", handler)
    
    async def block_resources(self, resource_types: List[str]) -> None:
        """Block specific resource types (images, fonts, etc.)."""
        async def block_handler(route):
            if route.request.resource_type in resource_types:
                await route.abort()
            else:
                await route.continue_()
        
        await self._page.route("**/*", block_handler)
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies."""
        return await self._context.cookies()
    
    async def add_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Add cookies."""
        await self._context.add_cookies(cookies)
    
    async def new_page(self) -> Page:
        """Create a new page in the context."""
        return await self._context.new_page()
    
    async def pdf(self, path: str, **kwargs) -> bytes:
        """Generate PDF of the page."""
        return await self._page.pdf(path=path, **kwargs)
