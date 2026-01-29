"""
Cloudflare Bypass Example - Scraping Cloudflare-protected sites.
"""

import asyncio
from scrape_thy_plaite import Scraper, ScraperConfig
from scrape_thy_plaite.core.config import EngineType, ConfigPresets
from scrape_thy_plaite.engines import CloudscraperEngine, UndetectedChromeEngine


async def cloudscraper_example():
    """
    Use CloudScraper to bypass Cloudflare JavaScript challenges.
    Works for most Cloudflare-protected sites.
    """
    print("=== CloudScraper Bypass Example ===\n")
    
    config = ConfigPresets.cloudflare_mode()
    
    async with Scraper(config) as scraper:
        try:
            result = await scraper.scrape(
                url="https://httpbin.org/get",  # Replace with CF-protected URL
                extract_html=True,
            )
            print(f"Success! Scraped: {result.url}")
            print(f"Response length: {len(result.html) if result.html else 0}")
        except Exception as e:
            print(f"Error: {e}")


async def undetected_chrome_example():
    """
    Use Undetected Chrome for sites with advanced bot detection.
    Best for sites that detect regular Selenium/Playwright.
    """
    print("\n=== Undetected Chrome Example ===\n")
    
    config = ScraperConfig(
        engine=EngineType.UNDETECTED_CHROME,
        browser={
            "headless": True,
            "window_size": (1920, 1080),
        },
        stealth={
            "enabled": True,
            "randomize_fingerprint": True,
            "mask_webdriver": True,
            "human_like_delays": True,
            "min_delay_ms": 500,
            "max_delay_ms": 1500,
        },
    )
    
    try:
        async with Scraper(config) as scraper:
            result = await scraper.scrape(
                url="https://nowsecure.nl/",  # Bot detection test site
                wait_for="body",
                take_screenshot=True,
            )
            print(f"Success! Scraped: {result.url}")
            
            if result.screenshot:
                # Save screenshot
                with open("cf_screenshot.png", "wb") as f:
                    f.write(result.screenshot)
                print("Screenshot saved to cf_screenshot.png")
                
    except Exception as e:
        print(f"Error (undetected-chromedriver may need to be installed): {e}")


async def cloudflare_with_cookies():
    """
    First get Cloudflare cookies with CloudScraper,
    then use them with a faster HTTP client.
    """
    print("\n=== Cloudflare Cookies Transfer Example ===\n")
    
    # Step 1: Get CF cookies with CloudScraper
    cf_config = ScraperConfig(engine=EngineType.CLOUDSCRAPER)
    
    try:
        async with CloudscraperEngine(cf_config) as cf_engine:
            await cf_engine.initialize()
            
            # Access the protected site
            await cf_engine.get("https://httpbin.org/cookies")
            
            # Get the Cloudflare tokens
            cookies = await cf_engine.get_cookies()
            print(f"Got cookies: {list(cookies.keys())}")
            
            # Step 2: Use cookies with HTTPX for faster requests
            fast_config = ScraperConfig(
                engine=EngineType.HTTPX,
                cookies=cookies,
            )
            
            async with Scraper(fast_config) as scraper:
                result = await scraper.scrape(
                    url="https://httpbin.org/cookies",
                )
                print(f"Fast request succeeded: {result.url}")
                
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all Cloudflare bypass examples."""
    await cloudscraper_example()
    # await undetected_chrome_example()  # Uncomment if UC is installed
    await cloudflare_with_cookies()


if __name__ == "__main__":
    asyncio.run(main())
