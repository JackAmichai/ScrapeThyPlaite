"""
Playwright Stealth Engine - Playwright with maximum anti-detection.
Uses playwright-stealth and custom evasion techniques.
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
    ConfigurationError,
)


# Comprehensive stealth scripts
STEALTH_SCRIPTS = """
// Webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
delete navigator.__proto__.webdriver;

// Chrome
window.chrome = {
    runtime: {},
    loadTimes: function() { return {}; },
    csi: function() { return {}; },
    app: { isInstalled: false }
};

// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ];
        plugins.length = 3;
        plugins.item = (i) => plugins[i];
        plugins.namedItem = (name) => plugins.find(p => p.name === name);
        plugins.refresh = () => {};
        return plugins;
    }
});

// Languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en', 'he']
});

// Platform
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});

// Hardware concurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8
});

// Device memory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8
});

// WebGL
const getParameterProxyHandler = {
    apply: function(target, thisArg, argumentsList) {
        const param = argumentsList[0];
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return target.apply(thisArg, argumentsList);
    }
};
try {
    WebGLRenderingContext.prototype.getParameter = new Proxy(
        WebGLRenderingContext.prototype.getParameter, getParameterProxyHandler
    );
    WebGL2RenderingContext.prototype.getParameter = new Proxy(
        WebGL2RenderingContext.prototype.getParameter, getParameterProxyHandler
    );
} catch(e) {}

// Canvas fingerprint protection
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' && this.width === 16 && this.height === 16) {
        // Likely fingerprinting attempt
        const context = this.getContext('2d');
        const imageData = context.getImageData(0, 0, this.width, this.height);
        for (let i = 0; i < imageData.data.length; i += 4) {
            imageData.data[i] ^= Math.floor(Math.random() * 2);
        }
        context.putImageData(imageData, 0, 0);
    }
    return originalToDataURL.apply(this, arguments);
};

// Audio fingerprint protection
const audioContextProto = window.AudioContext || window.webkitAudioContext;
if (audioContextProto) {
    const originalCreateAnalyser = audioContextProto.prototype.createAnalyser;
    audioContextProto.prototype.createAnalyser = function() {
        const analyser = originalCreateAnalyser.apply(this, arguments);
        const originalGetFloatFrequencyData = analyser.getFloatFrequencyData.bind(analyser);
        analyser.getFloatFrequencyData = function(array) {
            originalGetFloatFrequencyData(array);
            for (let i = 0; i < array.length; i++) {
                array[i] = array[i] + Math.random() * 0.0001;
            }
        };
        return analyser;
    };
}

// Notification
if (!window.Notification) {
    window.Notification = {
        permission: 'default',
        requestPermission: async () => 'default'
    };
}

// Battery API - return nothing to prevent fingerprinting
if (navigator.getBattery) {
    navigator.getBattery = async () => ({
        charging: true,
        chargingTime: 0,
        dischargingTime: Infinity,
        level: 1
    });
}

// Connection API
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '4g',
        rtt: 50,
        downlink: 10,
        saveData: false
    })
});

// Remove automation indicators in window
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
"""


class PlaywrightStealthEngine(BaseScraper):
    """
    Playwright with maximum stealth capabilities.
    
    Features:
    - Comprehensive anti-detection scripts
    - Canvas/WebGL fingerprint randomization
    - Audio context fingerprint protection
    - Human-like mouse movements
    - Realistic typing patterns
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
        """Initialize stealth browser."""
        self._playwright = await async_playwright().start()
        
        # Use Chromium for best compatibility
        browser_type = self._playwright.chromium
        
        # Launch options
        launch_options = {
            "headless": self.config.browser.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        }
        
        # Proxy
        if self.config.proxy.enabled and self.config.proxy.proxies:
            proxy = random.choice(self.config.proxy.proxies)
            launch_options["proxy"] = {"server": proxy}
        
        self._browser = await browser_type.launch(**launch_options)
        
        # Context options
        width, height = self.config.browser.window_size
        context_options = {
            "viewport": {"width": width, "height": height},
            "locale": self.config.browser.locale or "en-US",
            "timezone_id": self.config.browser.timezone or "America/New_York",
            "permissions": ["geolocation"],
            "geolocation": self.config.browser.geolocation or {"latitude": 40.7128, "longitude": -74.0060},
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "forced_colors": "none",
        }
        
        # User agent
        if self.config.browser.user_agent:
            context_options["user_agent"] = self.config.browser.user_agent
        elif self.config.stealth.randomize_user_agent:
            from scrape_thy_plaite.stealth.headers import get_random_user_agent
            context_options["user_agent"] = get_random_user_agent()
        else:
            context_options["user_agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        
        self._context = await self._browser.new_context(**context_options)
        
        # Add stealth scripts to run on every page
        await self._context.add_init_script(STEALTH_SCRIPTS)
        
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.timeout * 1000)
        
        self._initialized = True
        logger.info("Playwright Stealth Engine initialized")
    
    async def close(self) -> None:
        """Close browser."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Playwright Stealth Engine closed")
    
    async def get(self, url: str, **kwargs) -> Any:
        """Navigate to URL with human-like behavior."""
        try:
            response = await self._page.goto(
                url,
                wait_until=kwargs.get("wait_until", "domcontentloaded"),
                timeout=self.config.page_load_timeout * 1000,
            )
            
            # Human-like delay
            if self.config.stealth.human_like_delays:
                await asyncio.sleep(random.uniform(
                    self.config.stealth.min_delay_ms / 1000,
                    self.config.stealth.max_delay_ms / 1000
                ))
                
                # Random mouse movement
                await self._random_mouse_move()
            
            return response
        except Exception as e:
            raise BrowserError(f"Navigation failed: {e}")
    
    async def _random_mouse_move(self) -> None:
        """Perform random mouse movements."""
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await self._page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def get_html(self, url: str, **kwargs) -> str:
        """Get HTML content."""
        return await self._page.content()
    
    async def extract(
        self, 
        selectors: Dict[str, str], 
        selector_type: str = "css"
    ) -> Dict[str, Any]:
        """Extract data."""
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
        return await self._page.screenshot(path=path, full_page=True)
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript."""
        return await self._page.evaluate(script)
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        selector_type: str = "css"
    ) -> Any:
        """Wait for element."""
        timeout = (timeout or self.config.timeout) * 1000
        
        try:
            if selector_type == "xpath":
                locator = self._page.locator(f"xpath={selector}")
            else:
                locator = self._page.locator(selector)
            
            await locator.wait_for(timeout=timeout)
            return locator
        except Exception:
            raise ElementNotFoundError(f"Element not found: {selector}", selector=selector)
    
    async def click(self, selector: str, **kwargs) -> None:
        """Click with human-like behavior."""
        locator = self._page.locator(selector)
        
        if self.config.stealth.human_like_delays:
            # Move mouse to element first
            box = await locator.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
                y = box["y"] + box["height"] / 2 + random.randint(-5, 5)
                await self._page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        await locator.click(**kwargs)
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        delay: int = None
    ) -> None:
        """Type with human-like delays."""
        if delay is None:
            delay = random.randint(50, 150)
        await self._page.type(selector, text, delay=delay)
    
    async def scroll_to_bottom(self, step: int = 300, delay: float = 0.5) -> None:
        """Scroll to bottom with human-like behavior."""
        while True:
            current_position = await self._page.evaluate("window.pageYOffset")
            max_position = await self._page.evaluate(
                "document.documentElement.scrollHeight - window.innerHeight"
            )
            
            if current_position >= max_position:
                break
            
            # Scroll by random amount
            scroll_amount = step + random.randint(-50, 50)
            await self._page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(delay + random.uniform(-0.1, 0.2))
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get cookies."""
        return await self._context.cookies()
    
    async def add_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Add cookies."""
        await self._context.add_cookies(cookies)
    
    async def wait_for_network_idle(self, timeout: int = 30000) -> None:
        """Wait for network to be idle."""
        await self._page.wait_for_load_state("networkidle", timeout=timeout)
