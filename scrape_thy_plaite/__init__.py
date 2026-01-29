"""
ScrapeThyPlaite - Advanced Web Scraping Framework
The most powerful open-source web scraping toolkit for AI companies.

Features:
- Multi-engine support (Selenium, Playwright, HTTPX, CloudScraper, etc.)
- Advanced protection bypass (Cloudflare, DataDome, Akamai, etc.)
- CAPTCHA solving (reCAPTCHA, hCaptcha, Turnstile, FunCaptcha)
- AI-powered data extraction (GPT-4, Claude)
- Distributed scraping with Redis
- Browser fingerprint rotation
- Real-time monitoring dashboard
- Vercel deployment ready
"""

__version__ = "2.0.0"
__author__ = "ScrapeThyPlaite Team"

# Core components
from scrape_thy_plaite.core.config import ScraperConfig
from scrape_thy_plaite.core.base_scraper import Scraper

# Standard engines
from scrape_thy_plaite.engines import (
    SeleniumEngine,
    PlaywrightEngine,
    UndetectedChromeEngine,
    CloudscraperEngine,
    HttpxEngine,
)

# Advanced bypass engines
from scrape_thy_plaite.engines.advanced import (
    TLSFingerprintEngine,
    DrissionPageEngine,
    PlaywrightStealthEngine,
    UltimateScraper,
)

# CAPTCHA solving
from scrape_thy_plaite.captcha import CaptchaSolver

# Proxy management
from scrape_thy_plaite.proxy import ProxyManager

# AI-powered extraction
from scrape_thy_plaite.ai import (
    OpenAIExtractor,
    AnthropicExtractor,
    SmartExtractor,
)

# Distributed scraping
from scrape_thy_plaite.distributed import (
    JobQueue,
    Worker,
    DistributedScraper,
)

# Session management
from scrape_thy_plaite.sessions import (
    SessionManager,
    SessionPool,
)

# Monitoring
from scrape_thy_plaite.monitoring import (
    MetricsCollector,
    MonitoringServer,
)

# Fingerprint rotation
from scrape_thy_plaite.fingerprint import (
    FingerprintGenerator,
    FingerprintRotator,
    FingerprintInjector,
)

# Anti-bot detection
from scrape_thy_plaite.stealth.antibot_detection import ProtectionDetector

__all__ = [
    # Version
    "__version__",
    
    # Core
    "Scraper",
    "ScraperConfig",
    
    # Standard Engines
    "SeleniumEngine",
    "PlaywrightEngine",
    "UndetectedChromeEngine",
    "CloudscraperEngine",
    "HttpxEngine",
    
    # Advanced Engines
    "TLSFingerprintEngine",
    "DrissionPageEngine",
    "PlaywrightStealthEngine",
    "UltimateScraper",
    
    # CAPTCHA
    "CaptchaSolver",
    
    # Proxy
    "ProxyManager",
    
    # AI Extraction
    "OpenAIExtractor",
    "AnthropicExtractor",
    "SmartExtractor",
    
    # Distributed
    "JobQueue",
    "Worker",
    "DistributedScraper",
    
    # Sessions
    "SessionManager",
    "SessionPool",
    
    # Monitoring
    "MetricsCollector",
    "MonitoringServer",
    
    # Fingerprinting
    "FingerprintGenerator",
    "FingerprintRotator",
    "FingerprintInjector",
    
    # Protection Detection
    "ProtectionDetector",
