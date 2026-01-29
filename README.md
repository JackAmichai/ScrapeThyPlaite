# 🕷️ ScrapeThyPlaite - Advanced Web Scraping Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 The Most Advanced Open-Source Web Scraping Framework

ScrapeThyPlaite is an enterprise-grade web scraping framework designed for AI companies and data scientists who need reliable, ethical, and powerful data extraction capabilities.

## ✨ Features

### 🛡️ Anti-Detection & Bypass Capabilities
- **Undetected Chrome Driver** - Bypasses bot detection systems
- **Cloudflare Bypass** - Navigate through Cloudflare protection
- **CAPTCHA Solving** - Integration with 2Captcha, Anti-Captcha, and CapMonster
- **Browser Fingerprint Randomization** - Evade fingerprinting techniques
- **TLS Fingerprint Spoofing** - Mimic real browser TLS signatures

### 🔄 Multi-Engine Support
- **Selenium** - Full browser automation
- **Playwright** - Modern async browser automation
- **Requests/HTTPX** - Fast HTTP client for simple scraping
- **Scrapy Integration** - Distributed crawling support

### 🌐 Proxy & Network
- **Rotating Proxy Support** - Automatic proxy rotation
- **Residential Proxy Integration** - Support for premium proxy providers
- **SOCKS5/HTTP(S) Proxies** - All proxy types supported
- **Automatic Retry with Backoff** - Smart retry mechanisms

### 🧠 Intelligent Scraping
- **AI-Powered Content Extraction** - LLM integration for smart parsing
- **Automatic Schema Detection** - Auto-detect data structures
- **JavaScript Rendering** - Full SPA support
- **Dynamic Content Waiting** - Smart element waiting strategies

### 📊 Data Processing
- **Multiple Export Formats** - JSON, CSV, Parquet, SQLite
- **Data Validation** - Pydantic models for data integrity
- **Deduplication** - Automatic duplicate detection
- **Rate Limiting** - Respectful scraping with configurable limits

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/JackAmichai/ScrapeThyPlaite.git
cd ScrapeThyPlaite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## 🚀 Quick Start

```python
from scrape_thy_plaite import Scraper, ScraperConfig

# Initialize with anti-detection
config = ScraperConfig(
    engine="undetected_chrome",
    proxy_rotation=True,
    captcha_solver="2captcha",
    respect_robots_txt=True
)

scraper = Scraper(config)

# Scrape with automatic protection bypass
data = await scraper.scrape(
    url="https://example.com",
    selectors={
        "title": "h1",
        "content": ".main-content",
        "links": "a[href]"
    }
)

print(data)
```

## 🔧 Advanced Usage

### Using Different Engines

```python
# Playwright (Async, Modern)
async with PlaywrightScraper() as scraper:
    page = await scraper.new_page(stealth=True)
    await page.goto("https://example.com")
    content = await page.content()

# Undetected Chrome (Selenium-based)
with UndetectedChromeScraper() as scraper:
    scraper.get("https://example.com")
    element = scraper.find_element(By.CSS_SELECTOR, ".data")

# CloudScraper (Cloudflare bypass)
with CloudflareScraper() as scraper:
    response = scraper.get("https://cloudflare-protected-site.com")
```

### CAPTCHA Solving

```python
from scrape_thy_plaite.captcha import CaptchaSolver

solver = CaptchaSolver(
    provider="2captcha",
    api_key="YOUR_API_KEY"
)

# Solve reCAPTCHA v2
solution = await solver.solve_recaptcha_v2(
    site_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
    page_url="https://example.com"
)

# Solve hCaptcha
solution = await solver.solve_hcaptcha(
    site_key="a5f74b19-9e45-...",
    page_url="https://example.com"
)
```

### Proxy Rotation

```python
from scrape_thy_plaite.proxy import ProxyManager

proxy_manager = ProxyManager(
    proxies=[
        "http://user:pass@proxy1.com:8080",
        "socks5://user:pass@proxy2.com:1080",
    ],
    rotation_strategy="round_robin",  # or "random", "least_used"
    health_check=True
)

scraper = Scraper(proxy_manager=proxy_manager)
```

## ⚖️ Legal & Ethical Use

This tool is designed for **legal and ethical** web scraping:

- ✅ Always respect `robots.txt`
- ✅ Implement rate limiting to avoid server overload
- ✅ Use for publicly available data only
- ✅ Comply with website Terms of Service
- ✅ CAPTCHA solving services are paid and legal
- ✅ Don't scrape personal/private data without consent

## 📁 Project Structure

```
ScrapeThyPlaite/
├── scrape_thy_plaite/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── selenium_engine.py
│   │   ├── playwright_engine.py
│   │   ├── undetected_chrome.py
│   │   ├── cloudscraper_engine.py
│   │   └── httpx_engine.py
│   ├── captcha/
│   │   ├── __init__.py
│   │   ├── base_solver.py
│   │   ├── two_captcha.py
│   │   ├── anticaptcha.py
│   │   └── capmonster.py
│   ├── proxy/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── providers.py
│   ├── stealth/
│   │   ├── __init__.py
│   │   ├── fingerprint.py
│   │   ├── headers.py
│   │   └── evasion.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── css_extractor.py
│   │   ├── xpath_extractor.py
│   │   └── ai_extractor.py
│   └── utils/
│       ├── __init__.py
│       ├── retry.py
│       ├── rate_limiter.py
│       └── export.py
├── examples/
│   ├── basic_scraping.py
│   ├── cloudflare_bypass.py
│   ├── captcha_solving.py
│   └── proxy_rotation.py
├── tests/
├── requirements.txt
├── setup.py
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate business purposes only. Users are responsible for ensuring their use complies with applicable laws and website terms of service.
