"""
Basic Scraping Example - Getting started with ScrapeThyPlaite.
"""

import asyncio
from scrape_thy_plaite import Scraper, ScraperConfig
from scrape_thy_plaite.core.config import EngineType, ConfigPresets


async def basic_example():
    """Basic scraping with default configuration."""
    print("=== Basic Scraping Example ===\n")
    
    # Create scraper with default config
    config = ScraperConfig(
        engine=EngineType.HTTPX,  # Fast HTTP client
        timeout=30,
        respect_robots_txt=True,
    )
    
    async with Scraper(config) as scraper:
        # Scrape a simple page
        result = await scraper.scrape(
            url="https://httpbin.org/html",
            selectors={
                "title": "h1",
                "paragraphs": "p",
            },
            extract_html=True
        )
        
        print(f"URL: {result.url}")
        print(f"Timestamp: {result.timestamp}")
        print(f"Data: {result.data}")
        print(f"HTML Length: {len(result.html) if result.html else 0} chars")


async def stealth_example():
    """Scraping with stealth mode for protected sites."""
    print("\n=== Stealth Mode Example ===\n")
    
    # Use stealth preset
    config = ConfigPresets.stealth_mode()
    
    async with Scraper(config) as scraper:
        result = await scraper.scrape(
            url="https://httpbin.org/headers",
            extract_html=True
        )
        
        print(f"Successfully accessed with stealth mode!")
        print(f"Response length: {len(result.html) if result.html else 0} chars")


async def multi_url_example():
    """Scraping multiple URLs with concurrency control."""
    print("\n=== Multi-URL Scraping Example ===\n")
    
    config = ScraperConfig(
        engine=EngineType.HTTPX,
        rate_limit={"enabled": True, "requests_per_second": 2},
    )
    
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
    ]
    
    async with Scraper(config) as scraper:
        async for result in scraper.scrape_multiple(urls, concurrency=2):
            print(f"Scraped: {result.url}")


async def browser_example():
    """Scraping JavaScript-heavy pages with browser automation."""
    print("\n=== Browser Automation Example ===\n")
    
    # Use Playwright for JS rendering
    config = ConfigPresets.javascript_heavy()
    
    try:
        async with Scraper(config) as scraper:
            result = await scraper.scrape(
                url="https://httpbin.org/html",
                wait_for="body",  # Wait for element
                take_screenshot=True,
            )
            
            print(f"Scraped with browser: {result.url}")
            if result.screenshot:
                print(f"Screenshot size: {len(result.screenshot)} bytes")
    except Exception as e:
        print(f"Browser example requires Playwright installed: {e}")


async def main():
    """Run all examples."""
    await basic_example()
    await stealth_example()
    await multi_url_example()
    # await browser_example()  # Uncomment if Playwright is installed


if __name__ == "__main__":
    asyncio.run(main())
