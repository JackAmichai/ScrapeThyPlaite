"""
CAPTCHA Solving Example - Solving various types of CAPTCHAs.
"""

import asyncio
import os
from scrape_thy_plaite import Scraper, ScraperConfig, CaptchaSolver
from scrape_thy_plaite.core.config import (
    EngineType, 
    CaptchaConfig, 
    CaptchaProvider
)
from scrape_thy_plaite.captcha import CaptchaType


# Get API keys from environment variables
TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "your_api_key_here")
ANTICAPTCHA_API_KEY = os.getenv("ANTICAPTCHA_API_KEY", "your_api_key_here")


async def solve_recaptcha_v2():
    """
    Solve reCAPTCHA v2 using 2Captcha service.
    """
    print("=== reCAPTCHA v2 Solving Example ===\n")
    
    # Example site with reCAPTCHA v2
    # Replace with actual site key and URL
    SITE_KEY = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
    PAGE_URL = "https://www.google.com/recaptcha/api2/demo"
    
    config = CaptchaConfig(
        enabled=True,
        provider=CaptchaProvider.TWO_CAPTCHA,
        api_key=TWOCAPTCHA_API_KEY,
        timeout=120,
    )
    
    solver = CaptchaSolver(config)
    
    try:
        # Check balance first
        balance = await solver.get_balance()
        print(f"Account balance: ${balance:.2f}")
        
        if balance < 0.01:
            print("Insufficient balance!")
            return
        
        # Solve the CAPTCHA
        print("Solving reCAPTCHA v2...")
        token = await solver.solve(
            site_key=SITE_KEY,
            captcha_type=CaptchaType.RECAPTCHA_V2,
            page_url=PAGE_URL,
        )
        
        print(f"CAPTCHA solved!")
        print(f"Token (first 50 chars): {token[:50]}...")
        
    except Exception as e:
        print(f"Error: {e}")


async def solve_recaptcha_v3():
    """
    Solve reCAPTCHA v3 (invisible CAPTCHA).
    """
    print("\n=== reCAPTCHA v3 Solving Example ===\n")
    
    SITE_KEY = "6LdKlZEpAAAAAAOQjzC2v_d36tWxCl6dWsozdSy9"
    PAGE_URL = "https://recaptcha-demo.appspot.com/recaptcha-v3-request-scores.php"
    
    config = CaptchaConfig(
        enabled=True,
        provider=CaptchaProvider.TWO_CAPTCHA,
        api_key=TWOCAPTCHA_API_KEY,
        timeout=120,
    )
    
    solver = CaptchaSolver(config)
    
    try:
        print("Solving reCAPTCHA v3...")
        token = await solver.solve(
            site_key=SITE_KEY,
            captcha_type=CaptchaType.RECAPTCHA_V3,
            page_url=PAGE_URL,
            action="verify",  # The action parameter from the site
            min_score=0.7,    # Minimum score required
        )
        
        print(f"CAPTCHA solved!")
        print(f"Token (first 50 chars): {token[:50]}...")
        
    except Exception as e:
        print(f"Error: {e}")


async def solve_hcaptcha():
    """
    Solve hCaptcha challenges.
    """
    print("\n=== hCaptcha Solving Example ===\n")
    
    SITE_KEY = "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2"
    PAGE_URL = "https://accounts.hcaptcha.com/demo"
    
    config = CaptchaConfig(
        enabled=True,
        provider=CaptchaProvider.TWO_CAPTCHA,
        api_key=TWOCAPTCHA_API_KEY,
        timeout=180,  # hCaptcha can take longer
    )
    
    solver = CaptchaSolver(config)
    
    try:
        print("Solving hCaptcha...")
        token = await solver.solve(
            site_key=SITE_KEY,
            captcha_type=CaptchaType.HCAPTCHA,
            page_url=PAGE_URL,
        )
        
        print(f"CAPTCHA solved!")
        print(f"Token (first 50 chars): {token[:50]}...")
        
    except Exception as e:
        print(f"Error: {e}")


async def solve_turnstile():
    """
    Solve Cloudflare Turnstile challenges.
    """
    print("\n=== Cloudflare Turnstile Solving Example ===\n")
    
    # Turnstile is Cloudflare's CAPTCHA alternative
    SITE_KEY = "0x4AAAAAAADnPIDROrmt1Wwj"
    PAGE_URL = "https://example.com"  # Replace with actual URL
    
    config = CaptchaConfig(
        enabled=True,
        provider=CaptchaProvider.TWO_CAPTCHA,
        api_key=TWOCAPTCHA_API_KEY,
        timeout=120,
    )
    
    solver = CaptchaSolver(config)
    
    try:
        print("Solving Turnstile...")
        token = await solver.solve(
            site_key=SITE_KEY,
            captcha_type=CaptchaType.TURNSTILE,
            page_url=PAGE_URL,
        )
        
        print(f"Turnstile solved!")
        print(f"Token (first 50 chars): {token[:50]}...")
        
    except Exception as e:
        print(f"Error: {e}")


async def scrape_with_captcha():
    """
    Full example: Scrape a page and solve CAPTCHA if encountered.
    """
    print("\n=== Full Scraping with CAPTCHA Example ===\n")
    
    config = ScraperConfig(
        engine=EngineType.PLAYWRIGHT,
        browser={"headless": True},
        captcha={
            "enabled": True,
            "provider": "2captcha",
            "api_key": TWOCAPTCHA_API_KEY,
            "timeout": 120,
        },
    )
    
    try:
        async with Scraper(config) as scraper:
            # This would be the page with CAPTCHA
            result = await scraper.scrape(
                url="https://www.google.com/recaptcha/api2/demo",
                wait_for="body",
            )
            
            # If there's a CAPTCHA, detect and solve it
            if "g-recaptcha" in (result.html or ""):
                print("CAPTCHA detected! Solving...")
                
                # Extract site key from page
                # In real scenario, parse the sitekey from HTML
                site_key = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
                
                token = await scraper.solve_captcha(
                    site_key=site_key,
                    captcha_type="recaptcha_v2",
                    page_url=result.url,
                )
                
                print(f"CAPTCHA solved, token received!")
                
                # Now inject the token and submit the form
                # This would be done via the browser engine
                
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run CAPTCHA examples (requires valid API key)."""
    print("NOTE: These examples require valid CAPTCHA solving API keys.")
    print("Set TWOCAPTCHA_API_KEY or ANTICAPTCHA_API_KEY environment variables.\n")
    
    if TWOCAPTCHA_API_KEY == "your_api_key_here":
        print("Please set a valid API key to run these examples.")
        print("Example: export TWOCAPTCHA_API_KEY=your_actual_key")
        return
    
    await solve_recaptcha_v2()
    # await solve_recaptcha_v3()
    # await solve_hcaptcha()
    # await solve_turnstile()
    # await scrape_with_captcha()


if __name__ == "__main__":
    asyncio.run(main())
