"""Scraping engines for ScrapeThyPlaite."""

from scrape_thy_plaite.engines.selenium_engine import SeleniumEngine
from scrape_thy_plaite.engines.playwright_engine import PlaywrightEngine
from scrape_thy_plaite.engines.undetected_chrome import UndetectedChromeEngine
from scrape_thy_plaite.engines.cloudscraper_engine import CloudscraperEngine
from scrape_thy_plaite.engines.httpx_engine import HttpxEngine

__all__ = [
    "SeleniumEngine",
    "PlaywrightEngine",
    "UndetectedChromeEngine",
    "CloudscraperEngine",
    "HttpxEngine",
]
