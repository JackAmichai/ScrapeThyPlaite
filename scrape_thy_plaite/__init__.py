"""
ScrapeThyPlaite - Advanced Web Scraping Framework
The most powerful open-source web scraping toolkit for AI companies.
"""

__version__ = "1.0.0"
__author__ = "ScrapeThyPlaite Team"

from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.base_scraper import Scraper
from scrape_thy_plaite.engines import (
    SeleniumEngine,
    PlaywrightEngine,
    UndetectedChromeEngine,
    CloudscraperEngine,
    HttpxEngine,
)
from scrape_thy_plaite.captcha import CaptchaSolver
from scrape_thy_plaite.proxy import ProxyManager

__all__ = [
    "Scraper",
    "ScraperConfig",
    "SeleniumEngine",
    "PlaywrightEngine",
    "UndetectedChromeEngine",
    "CloudscraperEngine",
    "HttpxEngine",
    "CaptchaSolver",
    "ProxyManager",
]
