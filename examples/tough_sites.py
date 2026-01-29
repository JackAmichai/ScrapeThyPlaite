"""
Example: Scraping Tough Sites (Madlan, Yad2, and other protected sites)

This example demonstrates how to use ScrapeThyPlaite's advanced capabilities
to scrape websites with strong anti-bot protections like DataDome, 
Imperva/Incapsula, and custom Israeli site protections.

LEGAL DISCLAIMER:
Always respect the website's robots.txt and Terms of Service.
This tool is for educational purposes and authorized scraping only.
Unauthorized scraping may violate laws and ToS.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from loguru import logger

# Import the advanced engines
from scrape_thy_plaite.engines import (
    UltimateScraper,
    SiteSpecificScraper,
    BypassStrategy,
    TLSFingerprintEngine,
    DrissionPageEngine,
    PlaywrightStealthEngine,
)
from scrape_thy_plaite.core.config import ScraperConfig


async def scrape_madlan():
    """
    Scrape Madlan.co.il - Israeli real estate portal.
    
    Madlan uses sophisticated protection including:
    - DataDome
    - JavaScript challenge
    - Fingerprinting
    """
    logger.info("=== Madlan.co.il Scraping Example ===")
    
    # Get site-specific scraper for Israeli sites
    scraper = await SiteSpecificScraper.for_israeli_sites()
    
    try:
        await scraper.initialize()
        
        # Example: Scrape apartment listings in Tel Aviv
        url = "https://www.madlan.co.il/for-sale/tel-aviv-yafo"
        
        result = await scraper.scrape(
            url,
            wait_for_selector="div[data-testid='listing-card']",
            timeout=60
        )
        
        if result["success"]:
            logger.success(f"Successfully loaded Madlan! Status: {result['status_code']}")
            
            # Extract listing data
            html = result["html"]
            logger.info(f"Page content length: {len(html)} characters")
            
            # You would parse the HTML here with BeautifulSoup
            # Example extraction:
            # from bs4 import BeautifulSoup
            # soup = BeautifulSoup(html, 'lxml')
            # listings = soup.select('div[data-testid="listing-card"]')
            
            # Save HTML for debugging
            with open("madlan_output.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved HTML to madlan_output.html")
            
        else:
            logger.error(f"Failed to scrape Madlan: {result.get('error')}")
            logger.info(f"Strategy used: {result.get('strategy_used')}")
            logger.info(f"Strategies tried: {result.get('strategies_tried')}")
            
    finally:
        await scraper.close()


async def scrape_yad2():
    """
    Scrape Yad2.co.il - Israeli classifieds site.
    
    Yad2 uses:
    - Rate limiting
    - Cookie challenges
    - Device fingerprinting
    """
    logger.info("=== Yad2.co.il Scraping Example ===")
    
    # Custom configuration for Yad2
    config = ScraperConfig(
        timeout=60,
        page_load_timeout=90,
        stealth={
            "enabled": True,
            "human_like_delays": True,
            "min_delay_ms": 2000,  # Longer delays
            "max_delay_ms": 5000,
            "randomize_user_agent": True,
        },
        browser={
            "headless": True,
            "window_size": (1920, 1080),
            "locale": "he-IL",
            "timezone": "Asia/Jerusalem",
        }
    )
    
    scraper = UltimateScraper(config)
    
    try:
        await scraper.initialize()
        
        # Start with less aggressive strategy
        scraper.set_strategy_order([
            BypassStrategy.TLS_FINGERPRINT,
            BypassStrategy.CLOUDSCRAPER,
            BypassStrategy.PLAYWRIGHT_STEALTH,
        ])
        
        url = "https://www.yad2.co.il/realestate/forsale"
        result = await scraper.scrape(url, timeout=60)
        
        if result["success"]:
            logger.success("Successfully loaded Yad2!")
            
        else:
            logger.error(f"Failed: {result.get('error')}")
            
    finally:
        await scraper.close()


async def scrape_with_manual_strategy():
    """
    Example of using individual engines directly for maximum control.
    """
    logger.info("=== Manual Strategy Example ===")
    
    # Try TLS fingerprinting first (fastest)
    logger.info("Strategy 1: TLS Fingerprint Engine")
    try:
        tls_engine = TLSFingerprintEngine()
        await tls_engine.initialize()
        
        response = await tls_engine.get("https://www.example.com")
        
        if response and response.status_code == 200:
            logger.success("TLS Fingerprint worked!")
            html = await tls_engine.get_html("https://www.example.com")
            return html
            
    except Exception as e:
        logger.warning(f"TLS Fingerprint failed: {e}")
    finally:
        await tls_engine.close()
    
    # Fall back to DrissionPage
    logger.info("Strategy 2: DrissionPage Engine")
    try:
        drission = DrissionPageEngine()
        await drission.initialize()
        
        response = await drission.get("https://www.example.com")
        
        if response:
            logger.success("DrissionPage worked!")
            html = await drission.get_html("https://www.example.com")
            return html
            
    except Exception as e:
        logger.warning(f"DrissionPage failed: {e}")
    finally:
        await drission.close()
    
    # Final fallback - Playwright Stealth
    logger.info("Strategy 3: Playwright Stealth Engine")
    try:
        playwright = PlaywrightStealthEngine()
        await playwright.initialize()
        
        response = await playwright.get("https://www.example.com")
        
        if response and response.ok:
            logger.success("Playwright Stealth worked!")
            html = await playwright.get_html("https://www.example.com")
            return html
            
    except Exception as e:
        logger.error(f"All strategies failed: {e}")
    finally:
        await playwright.close()
    
    return None


async def scrape_protected_api():
    """
    Example of scraping a protected API endpoint.
    
    Many sites load data via API calls that are easier to scrape
    than rendered HTML once you have valid cookies/headers.
    """
    logger.info("=== Protected API Scraping Example ===")
    
    # First, load the main page to get cookies and headers
    config = ScraperConfig(
        stealth={"enabled": True, "human_like_delays": True}
    )
    
    scraper = SiteSpecificScraper.for_cloudflare(config)
    
    try:
        await scraper.initialize()
        
        # Load main page first
        main_url = "https://example-api-site.com"
        result = await scraper.scrape(main_url)
        
        if result["success"]:
            # Now use the same session to call API
            api_url = "https://example-api-site.com/api/listings"
            
            # The session should now have valid cookies
            api_result = await scraper.scrape(api_url)
            
            if api_result["success"]:
                try:
                    data = json.loads(api_result["html"])
                    logger.success(f"Got API data: {len(data)} items")
                    return data
                except json.JSONDecodeError:
                    logger.warning("Response is not JSON")
                    
    finally:
        await scraper.close()


class MadlanScraper:
    """
    Specialized scraper for Madlan.co.il.
    
    This class provides high-level methods for common Madlan operations.
    """
    
    def __init__(self, headless: bool = True):
        self.config = ScraperConfig(
            timeout=60,
            page_load_timeout=90,
            stealth={
                "enabled": True,
                "human_like_delays": True,
                "min_delay_ms": 2000,
                "max_delay_ms": 4000,
            },
            browser={
                "headless": headless,
                "locale": "he-IL",
                "timezone": "Asia/Jerusalem",
            }
        )
        self.scraper: Optional[UltimateScraper] = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize the scraper."""
        self.scraper = await SiteSpecificScraper.for_israeli_sites(self.config)
        await self.scraper.initialize()
    
    async def close(self):
        """Close the scraper."""
        if self.scraper:
            await self.scraper.close()
    
    async def search_apartments(
        self,
        city: str,
        for_sale: bool = True,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search apartments on Madlan.
        
        Args:
            city: City name (in English, e.g., "tel-aviv-yafo")
            for_sale: True for sale, False for rent
            min_price: Minimum price
            max_price: Maximum price
            min_rooms: Minimum rooms
            max_rooms: Maximum rooms
            
        Returns:
            List of apartment dictionaries
        """
        # Build URL
        listing_type = "for-sale" if for_sale else "for-rent"
        url = f"https://www.madlan.co.il/{listing_type}/{city}"
        
        # Add query parameters
        params = []
        if min_price:
            params.append(f"minPrice={min_price}")
        if max_price:
            params.append(f"maxPrice={max_price}")
        if min_rooms:
            params.append(f"minRooms={min_rooms}")
        if max_rooms:
            params.append(f"maxRooms={max_rooms}")
        
        if params:
            url += "?" + "&".join(params)
        
        logger.info(f"Searching: {url}")
        
        result = await self.scraper.scrape(
            url,
            wait_for_selector="div[data-testid='listing-card']",
            timeout=60
        )
        
        if not result["success"]:
            logger.error(f"Search failed: {result.get('error')}")
            return []
        
        # Parse results (you would implement actual parsing here)
        # This is a placeholder - actual implementation depends on Madlan's HTML structure
        return self._parse_listings(result["html"])
    
    def _parse_listings(self, html: str) -> List[Dict[str, Any]]:
        """Parse apartment listings from HTML."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'lxml')
            listings = []
            
            for card in soup.select('div[data-testid="listing-card"]'):
                listing = {}
                
                # Extract price
                price_el = card.select_one('[data-testid="listing-price"]')
                if price_el:
                    listing["price"] = price_el.get_text(strip=True)
                
                # Extract address
                addr_el = card.select_one('[data-testid="listing-address"]')
                if addr_el:
                    listing["address"] = addr_el.get_text(strip=True)
                
                # Extract rooms
                rooms_el = card.select_one('[data-testid="listing-rooms"]')
                if rooms_el:
                    listing["rooms"] = rooms_el.get_text(strip=True)
                
                # Extract size
                size_el = card.select_one('[data-testid="listing-size"]')
                if size_el:
                    listing["size"] = size_el.get_text(strip=True)
                
                # Extract link
                link_el = card.select_one('a[href*="/listing/"]')
                if link_el:
                    listing["url"] = "https://www.madlan.co.il" + link_el["href"]
                
                if listing:
                    listings.append(listing)
            
            return listings
            
        except ImportError:
            logger.warning("BeautifulSoup not available for parsing")
            return []
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return []
    
    async def get_listing_details(self, listing_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific listing."""
        result = await self.scraper.scrape(
            listing_url,
            wait_for_selector="div[data-testid='listing-details']",
            timeout=60
        )
        
        if not result["success"]:
            return {"error": result.get("error")}
        
        # Parse details (placeholder)
        return self._parse_listing_details(result["html"])
    
    def _parse_listing_details(self, html: str) -> Dict[str, Any]:
        """Parse listing details from HTML."""
        # Implement actual parsing based on Madlan's structure
        return {"html_length": len(html)}


async def main():
    """Run examples."""
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("\n" + "=" * 60)
    print("ScrapeThyPlaite - Tough Sites Scraping Examples")
    print("=" * 60 + "\n")
    
    # Uncomment the example you want to run:
    
    # Example 1: Scrape Madlan
    # await scrape_madlan()
    
    # Example 2: Scrape Yad2
    # await scrape_yad2()
    
    # Example 3: Manual strategy control
    # html = await scrape_with_manual_strategy()
    
    # Example 4: Using MadlanScraper class
    # async with MadlanScraper(headless=True) as scraper:
    #     apartments = await scraper.search_apartments(
    #         city="tel-aviv-yafo",
    #         for_sale=True,
    #         min_price=1000000,
    #         max_price=3000000,
    #         min_rooms=3
    #     )
    #     print(f"Found {len(apartments)} apartments")
    #     for apt in apartments[:5]:
    #         print(apt)
    
    print("\nExamples are commented out. Uncomment the one you want to run.")
    print("Make sure to respect robots.txt and Terms of Service!")


if __name__ == "__main__":
    asyncio.run(main())
