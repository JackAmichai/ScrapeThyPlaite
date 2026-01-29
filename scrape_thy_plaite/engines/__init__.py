"""Scraping engines for ScrapeThyPlaite."""

# Basic engines
from scrape_thy_plaite.engines.selenium_engine import SeleniumEngine
from scrape_thy_plaite.engines.playwright_engine import PlaywrightEngine
from scrape_thy_plaite.engines.undetected_chrome import UndetectedChromeEngine
from scrape_thy_plaite.engines.cloudscraper_engine import CloudscraperEngine
from scrape_thy_plaite.engines.httpx_engine import HttpxEngine

# Advanced anti-detection engines
from scrape_thy_plaite.engines.tls_fingerprint import TLSFingerprintEngine
from scrape_thy_plaite.engines.drission_engine import DrissionPageEngine
from scrape_thy_plaite.engines.playwright_stealth import PlaywrightStealthEngine
from scrape_thy_plaite.engines.ultimate_scraper import (
    UltimateScraper,
    SiteSpecificScraper,
    BypassStrategy,
)

__all__ = [
    # Basic engines
    "SeleniumEngine",
    "PlaywrightEngine",
    "UndetectedChromeEngine",
    "CloudscraperEngine",
    "HttpxEngine",
    # Advanced engines
    "TLSFingerprintEngine",
    "DrissionPageEngine",
    "PlaywrightStealthEngine",
    "UltimateScraper",
    "SiteSpecificScraper",
    "BypassStrategy",
]
