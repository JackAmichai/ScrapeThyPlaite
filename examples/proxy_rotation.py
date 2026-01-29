"""
Proxy Rotation Example - Using proxy pools for distributed scraping.
"""

import asyncio
from scrape_thy_plaite import Scraper, ScraperConfig, ProxyManager
from scrape_thy_plaite.core.config import EngineType
from scrape_thy_plaite.proxy import ProxyProviders


async def basic_proxy_rotation():
    """
    Basic proxy rotation with a list of proxies.
    """
    print("=== Basic Proxy Rotation Example ===\n")
    
    # Your proxy list (replace with actual proxies)
    proxies = [
        "http://user1:pass1@proxy1.example.com:8080",
        "http://user2:pass2@proxy2.example.com:8080",
        "socks5://user3:pass3@proxy3.example.com:1080",
    ]
    
    # Create proxy manager
    proxy_manager = ProxyManager(
        proxies=proxies,
        rotation_strategy="round_robin",
        health_check=True,
    )
    
    # Health check all proxies
    print("Performing health check...")
    results = await proxy_manager.health_check_all()
    
    for proxy_url, healthy in results.items():
        status = "✓ Healthy" if healthy else "✗ Unhealthy"
        print(f"  {proxy_url}: {status}")
    
    # Get proxy for request
    proxy = await proxy_manager.get_proxy()
    if proxy:
        print(f"\nUsing proxy: {proxy.host}:{proxy.port}")
    
    # Report result
    await proxy_manager.report_result(proxy, success=True, response_time=0.5)
    
    # Show stats
    stats = proxy_manager.get_stats()
    print(f"\nProxy Pool Stats:")
    print(f"  Total: {stats['total_proxies']}")
    print(f"  Healthy: {stats['healthy_proxies']}")


async def scraping_with_proxies():
    """
    Scraping multiple URLs with automatic proxy rotation.
    """
    print("\n=== Scraping with Proxy Rotation ===\n")
    
    # For demo, we'll use httpbin to show different IPs
    config = ScraperConfig(
        engine=EngineType.HTTPX,
        proxy={
            "enabled": True,
            "proxies": [
                # Add your proxies here
                # "http://user:pass@proxy.example.com:8080",
            ],
            "rotation_strategy": "round_robin",
            "health_check": True,
        },
        rate_limit={
            "enabled": True,
            "requests_per_second": 1,
        },
    )
    
    async with Scraper(config) as scraper:
        urls = [
            "https://httpbin.org/ip",
            "https://httpbin.org/ip",
            "https://httpbin.org/ip",
        ]
        
        async for result in scraper.scrape_multiple(urls, concurrency=1):
            print(f"Scraped {result.url}")
            print(f"  Response: {result.data}")


async def residential_proxy_example():
    """
    Using residential proxy providers (Bright Data, Oxylabs, etc.)
    """
    print("\n=== Residential Proxy Providers ===\n")
    
    # Example with Bright Data (formerly Luminati)
    bright_data_proxy = ProxyProviders.bright_data(
        username="your_username",
        password="your_password",
        zone="residential",
        country="us",
        session_id="session123"  # For sticky sessions
    )
    print(f"Bright Data URL: {bright_data_proxy}")
    
    # Example with Oxylabs
    oxylabs_proxy = ProxyProviders.oxylabs(
        username="your_username",
        password="your_password",
        country="us",
        city="new_york",
    )
    print(f"Oxylabs URL: {oxylabs_proxy}")
    
    # Example with Smartproxy
    smartproxy = ProxyProviders.smartproxy(
        username="your_username",
        password="your_password",
        country="us",
        session_type="rotating",
    )
    print(f"Smartproxy URL: {smartproxy}")


async def sticky_sessions():
    """
    Using sticky sessions to maintain the same IP for a session.
    """
    print("\n=== Sticky Sessions Example ===\n")
    
    proxies = [
        "http://user:pass@proxy1.example.com:8080",
        "http://user:pass@proxy2.example.com:8080",
    ]
    
    proxy_manager = ProxyManager(
        proxies=proxies,
        rotation_strategy="sticky",
        health_check=False,
    )
    
    # Session 1 - always gets same proxy
    session1_proxy = await proxy_manager.get_proxy(session_id="user_123")
    print(f"Session 1 proxy: {session1_proxy.host if session1_proxy else 'None'}")
    
    # Session 2 - gets different proxy
    session2_proxy = await proxy_manager.get_proxy(session_id="user_456")
    print(f"Session 2 proxy: {session2_proxy.host if session2_proxy else 'None'}")
    
    # Session 1 again - same proxy as before
    session1_proxy_again = await proxy_manager.get_proxy(session_id="user_123")
    print(f"Session 1 again: {session1_proxy_again.host if session1_proxy_again else 'None'}")


async def adaptive_proxy_usage():
    """
    Using adaptive rate limiting based on proxy responses.
    """
    print("\n=== Adaptive Proxy Management ===\n")
    
    from scrape_thy_plaite.utils.rate_limiter import AdaptiveRateLimiter
    from scrape_thy_plaite.core.config import RateLimitConfig
    
    # Create adaptive rate limiter
    rate_config = RateLimitConfig(
        enabled=True,
        requests_per_second=2.0,
    )
    limiter = AdaptiveRateLimiter(rate_config)
    
    domain = "example.com"
    
    # Simulate successful requests
    for i in range(12):
        await limiter.acquire(domain)
        limiter.report_success(domain)
        print(f"Request {i+1}: Success")
    
    # Simulate rate limit hit
    limiter.report_rate_limit(domain, retry_after=5)
    print("\nRate limit hit! Limiter will slow down automatically.")
    
    # Check the reduced rate
    wait_time = limiter.get_wait_time(domain)
    print(f"Wait time after rate limit: {wait_time:.2f}s")


async def main():
    """Run all proxy examples."""
    await basic_proxy_rotation()
    await scraping_with_proxies()
    await residential_proxy_example()
    await sticky_sessions()
    await adaptive_proxy_usage()


if __name__ == "__main__":
    asyncio.run(main())
