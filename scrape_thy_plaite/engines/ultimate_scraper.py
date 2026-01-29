"""
Ultimate Scraper - Multi-layer approach for maximum bypass capability.
Combines multiple techniques to scrape even the most protected sites.
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import random
import time

from loguru import logger

from scrape_thy_plaite.core.config import ScraperConfig, EngineType
from scrape_thy_plaite.core.exceptions import (
    BlockedError,
    ScraperException,
    ConfigurationError,
)
from scrape_thy_plaite.core.base_scraper import BaseScraper, ScrapedData


class BypassStrategy(str, Enum):
    """Available bypass strategies."""
    TLS_FINGERPRINT = "tls_fingerprint"
    UNDETECTED_CHROME = "undetected_chrome"
    DRISSION_PAGE = "drission_page"
    CLOUDSCRAPER = "cloudscraper"
    PLAYWRIGHT_STEALTH = "playwright_stealth"
    BROWSER_POOL = "browser_pool"


class UltimateScraper:
    """
    Ultimate Scraper - The most advanced scraping solution.
    
    This scraper uses a multi-layer approach:
    1. First tries TLS fingerprint spoofing (fastest)
    2. Falls back to CloudScraper if blocked
    3. Falls back to Undetected Chrome if still blocked
    4. Falls back to DrissionPage for maximum stealth
    5. Uses Playwright with stealth as final resort
    
    Features:
    - Automatic strategy rotation on blocks
    - Smart retry with different engines
    - Session persistence across engines
    - Cookie transfer between engines
    - Adaptive rate limiting
    - Human behavior simulation
    """
    
    def __init__(
        self, 
        config: Optional[ScraperConfig] = None,
        strategies: Optional[List[BypassStrategy]] = None
    ):
        self.config = config or ScraperConfig()
        
        # Default strategy order (fastest to most powerful)
        self.strategies = strategies or [
            BypassStrategy.TLS_FINGERPRINT,
            BypassStrategy.CLOUDSCRAPER,
            BypassStrategy.UNDETECTED_CHROME,
            BypassStrategy.PLAYWRIGHT_STEALTH,
        ]
        
        self._engines: Dict[BypassStrategy, BaseScraper] = {}
        self._current_strategy: Optional[BypassStrategy] = None
        self._cookies: Dict[str, str] = {}
        self._blocked_strategies: List[BypassStrategy] = []
    
    async def initialize(self) -> None:
        """Initialize the first available engine."""
        for strategy in self.strategies:
            try:
                engine = await self._create_engine(strategy)
                await engine.initialize()
                self._engines[strategy] = engine
                self._current_strategy = strategy
                logger.info(f"UltimateScraper initialized with {strategy.value}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize {strategy.value}: {e}")
                continue
        
        raise ConfigurationError("No scraping engines could be initialized")
    
    async def _create_engine(self, strategy: BypassStrategy) -> BaseScraper:
        """Create engine for the given strategy."""
        if strategy == BypassStrategy.TLS_FINGERPRINT:
            from scrape_thy_plaite.engines.tls_fingerprint import TLSFingerprintEngine
            return TLSFingerprintEngine(self.config)
        
        elif strategy == BypassStrategy.CLOUDSCRAPER:
            from scrape_thy_plaite.engines.cloudscraper_engine import CloudscraperEngine
            return CloudscraperEngine(self.config)
        
        elif strategy == BypassStrategy.UNDETECTED_CHROME:
            from scrape_thy_plaite.engines.undetected_chrome import UndetectedChromeEngine
            return UndetectedChromeEngine(self.config)
        
        elif strategy == BypassStrategy.PLAYWRIGHT_STEALTH:
            from scrape_thy_plaite.engines.playwright_stealth import PlaywrightStealthEngine
            return PlaywrightStealthEngine(self.config)
        
        elif strategy == BypassStrategy.DRISSION_PAGE:
            from scrape_thy_plaite.engines.drission_engine import DrissionPageEngine
            return DrissionPageEngine(self.config)
        
        raise ConfigurationError(f"Unknown strategy: {strategy}")
    
    async def _get_engine(self, strategy: BypassStrategy) -> BaseScraper:
        """Get or create engine for strategy."""
        if strategy not in self._engines:
            engine = await self._create_engine(strategy)
            await engine.initialize()
            self._engines[strategy] = engine
        return self._engines[strategy]
    
    async def _escalate_strategy(self) -> bool:
        """
        Escalate to a more powerful strategy.
        
        Returns:
            True if escalation successful, False if no more strategies
        """
        current_idx = self.strategies.index(self._current_strategy)
        
        # Mark current as blocked
        if self._current_strategy not in self._blocked_strategies:
            self._blocked_strategies.append(self._current_strategy)
        
        # Find next available strategy
        for i in range(current_idx + 1, len(self.strategies)):
            strategy = self.strategies[i]
            if strategy not in self._blocked_strategies:
                try:
                    await self._get_engine(strategy)
                    self._current_strategy = strategy
                    logger.info(f"Escalated to strategy: {strategy.value}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to escalate to {strategy.value}: {e}")
                    continue
        
        return False
    
    async def close(self) -> None:
        """Close all engines."""
        for strategy, engine in self._engines.items():
            try:
                await engine.close()
            except Exception as e:
                logger.warning(f"Error closing {strategy.value}: {e}")
        self._engines.clear()
        logger.info("UltimateScraper closed")
    
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
        max_retries: int = 3,
        **kwargs
    ) -> ScrapedData:
        """
        Scrape a URL with automatic strategy escalation.
        
        Args:
            url: URL to scrape
            selectors: Data selectors
            wait_for: Element to wait for
            max_retries: Max retries per strategy
            **kwargs: Additional arguments
            
        Returns:
            ScrapedData with extracted content
        """
        from datetime import datetime
        
        last_error = None
        attempts = 0
        
        while True:
            engine = self._engines.get(self._current_strategy)
            if not engine:
                engine = await self._get_engine(self._current_strategy)
            
            for retry in range(max_retries):
                try:
                    logger.info(f"Attempting {url} with {self._current_strategy.value} (attempt {retry + 1})")
                    
                    # Add human-like delay
                    if retry > 0:
                        await asyncio.sleep(random.uniform(2, 5))
                    
                    # Make request
                    html = await engine.get(url, **kwargs)
                    
                    # Wait for element if specified
                    if wait_for:
                        await engine.wait_for_element(wait_for)
                    
                    # Get final HTML
                    if isinstance(html, str):
                        final_html = html
                    else:
                        final_html = await engine.get_html(url)
                    
                    # Extract data
                    data = {}
                    if selectors:
                        data = await engine.extract(selectors)
                    
                    # Success!
                    logger.info(f"Successfully scraped {url}")
                    
                    return ScrapedData(
                        url=url,
                        timestamp=datetime.now(),
                        data=data,
                        html=final_html,
                        fingerprint=f"{self._current_strategy.value}_{engine.session_id}",
                    )
                    
                except BlockedError as e:
                    logger.warning(f"Blocked on {self._current_strategy.value}: {e}")
                    last_error = e
                    break  # Try next strategy
                    
                except Exception as e:
                    logger.warning(f"Error on attempt {retry + 1}: {e}")
                    last_error = e
                    if retry < max_retries - 1:
                        continue
                    break  # Try next strategy
            
            # Try to escalate to next strategy
            if not await self._escalate_strategy():
                # No more strategies
                raise ScraperException(
                    f"All strategies exhausted for {url}",
                    details={"last_error": str(last_error)}
                )
    
    async def scrape_with_browser(
        self,
        url: str,
        actions: Optional[List[Dict[str, Any]]] = None,
        selectors: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> ScrapedData:
        """
        Scrape with browser, executing actions (clicks, typing, etc.)
        
        Args:
            url: URL to scrape
            actions: List of actions to perform
                [{"type": "click", "selector": "#button"},
                 {"type": "type", "selector": "#input", "text": "hello"},
                 {"type": "wait", "seconds": 2},
                 {"type": "scroll", "direction": "bottom"}]
            selectors: Data selectors
        """
        # Force browser-based strategy
        browser_strategies = [
            BypassStrategy.UNDETECTED_CHROME,
            BypassStrategy.PLAYWRIGHT_STEALTH,
            BypassStrategy.DRISSION_PAGE,
        ]
        
        engine = None
        for strategy in browser_strategies:
            if strategy in self._engines:
                engine = self._engines[strategy]
                break
            try:
                engine = await self._get_engine(strategy)
                break
            except Exception:
                continue
        
        if not engine:
            raise ConfigurationError("No browser engine available")
        
        from datetime import datetime
        
        # Navigate
        await engine.get(url, **kwargs)
        
        # Execute actions
        if actions:
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "click":
                    await engine.click(action["selector"])
                elif action_type == "type":
                    await engine.type_text(action["selector"], action["text"])
                elif action_type == "wait":
                    await asyncio.sleep(action.get("seconds", 1))
                elif action_type == "scroll":
                    if action.get("direction") == "bottom":
                        await engine.scroll_to_bottom()
                elif action_type == "wait_for":
                    await engine.wait_for_element(action["selector"])
        
        # Extract data
        html = await engine.get_html(url)
        data = {}
        if selectors:
            data = await engine.extract(selectors)
        
        return ScrapedData(
            url=url,
            timestamp=datetime.now(),
            data=data,
            html=html,
        )


class SiteSpecificScraper:
    """
    Pre-configured scrapers for known difficult sites.
    """
    
    @staticmethod
    def for_cloudflare() -> UltimateScraper:
        """Scraper optimized for Cloudflare-protected sites."""
        config = ScraperConfig(
            stealth={"enabled": True, "human_like_delays": True},
            rate_limit={"enabled": True, "requests_per_second": 0.5},
        )
        return UltimateScraper(
            config=config,
            strategies=[
                BypassStrategy.CLOUDSCRAPER,
                BypassStrategy.TLS_FINGERPRINT,
                BypassStrategy.UNDETECTED_CHROME,
            ]
        )
    
    @staticmethod
    def for_akamai() -> UltimateScraper:
        """Scraper optimized for Akamai-protected sites."""
        config = ScraperConfig(
            stealth={
                "enabled": True,
                "human_like_delays": True,
                "randomize_fingerprint": True,
                "min_delay_ms": 1000,
                "max_delay_ms": 3000,
            },
        )
        return UltimateScraper(
            config=config,
            strategies=[
                BypassStrategy.TLS_FINGERPRINT,
                BypassStrategy.UNDETECTED_CHROME,
                BypassStrategy.PLAYWRIGHT_STEALTH,
            ]
        )
    
    @staticmethod
    def for_datadome() -> UltimateScraper:
        """Scraper optimized for DataDome-protected sites."""
        config = ScraperConfig(
            stealth={
                "enabled": True,
                "human_like_delays": True,
                "randomize_fingerprint": True,
            },
            browser={"headless": False},  # DataDome often detects headless
        )
        return UltimateScraper(
            config=config,
            strategies=[
                BypassStrategy.UNDETECTED_CHROME,
                BypassStrategy.DRISSION_PAGE,
            ]
        )
    
    @staticmethod
    def for_perimeter_x() -> UltimateScraper:
        """Scraper optimized for PerimeterX-protected sites."""
        config = ScraperConfig(
            stealth={
                "enabled": True,
                "human_like_delays": True,
                "randomize_fingerprint": True,
                "mask_webdriver": True,
                "spoof_webgl": True,
            },
        )
        return UltimateScraper(
            config=config,
            strategies=[
                BypassStrategy.TLS_FINGERPRINT,
                BypassStrategy.UNDETECTED_CHROME,
                BypassStrategy.PLAYWRIGHT_STEALTH,
            ]
        )
    
    @staticmethod
    def for_israeli_sites() -> UltimateScraper:
        """Scraper optimized for Israeli sites (Madlan, Yad2, etc.)."""
        config = ScraperConfig(
            stealth={
                "enabled": True,
                "human_like_delays": True,
                "randomize_fingerprint": True,
                "min_delay_ms": 1500,
                "max_delay_ms": 4000,
            },
            browser={
                "headless": False,
                "locale": "he-IL",
            },
            rate_limit={
                "enabled": True,
                "requests_per_second": 0.3,
            },
        )
        return UltimateScraper(
            config=config,
            strategies=[
                BypassStrategy.TLS_FINGERPRINT,
                BypassStrategy.UNDETECTED_CHROME,
                BypassStrategy.PLAYWRIGHT_STEALTH,
            ]
        )
