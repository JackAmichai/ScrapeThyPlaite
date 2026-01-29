"""Core module for ScrapeThyPlaite."""

from scrape_thy_plaite.core.config import ScraperConfig, ConfigPresets, EngineType
from scrape_thy_plaite.core.base_scraper import Scraper, BaseScraper, ScrapedData
from scrape_thy_plaite.core.exceptions import *

__all__ = [
    "ScraperConfig",
    "ConfigPresets",
    "EngineType",
    "Scraper",
    "BaseScraper",
    "ScrapedData",
]
