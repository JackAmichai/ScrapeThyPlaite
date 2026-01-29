"""
Vercel Serverless API - Single URL Scraping Endpoint
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import time
import asyncio
from urllib.parse import urlparse


def verify_api_key(headers):
    """Verify API key if configured."""
    required_key = os.environ.get("SCRAPER_API_KEY")
    if required_key:
        provided_key = headers.get("X-Api-Key") or headers.get("x-api-key")
        if provided_key != required_key:
            return False
    return True


def get_event_loop():
    """Get or create event loop."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # Verify API key
        if not verify_api_key(dict(self.headers)):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid API key"}).encode())
            return
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        # Validate URL
        url = request_data.get("url")
        if not url:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URL is required"}).encode())
            return
        
        # Parse options
        options = {
            "javascript": request_data.get("javascript", False),
            "timeout": request_data.get("timeout", 30),
            "bypass_protection": request_data.get("bypass_protection", True),
            "extract": request_data.get("extract"),
            "headers": request_data.get("headers", {}),
            "proxy": request_data.get("proxy"),
        }
        
        # Perform scraping
        start_time = time.time()
        
        try:
            # Use appropriate scraper based on serverless constraints
            result = self.scrape_url(url, options)
            response_time = (time.time() - start_time) * 1000
            
            response = {
                "success": result.get("success", False),
                "url": url,
                "status_code": result.get("status_code"),
                "html": result.get("html"),
                "extracted_data": result.get("extracted_data"),
                "protection_detected": result.get("protection"),
                "bypass_strategy": result.get("strategy"),
                "response_time_ms": round(response_time, 2),
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "url": url,
                "error": str(e),
                "response_time_ms": round(response_time, 2),
            }).encode())
    
    def scrape_url(self, url: str, options: dict) -> dict:
        """
        Scrape URL using serverless-compatible methods.
        
        Vercel serverless functions have limitations:
        - No persistent browser instances
        - 10-60 second timeout
        - Limited memory
        
        We use lightweight HTTP-based scrapers.
        """
        import requests
        
        # Try CloudScraper first (handles Cloudflare)
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True,
                }
            )
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            headers.update(options.get("headers", {}))
            
            response = scraper.get(
                url,
                headers=headers,
                timeout=options.get("timeout", 30),
                proxies={"http": options["proxy"], "https": options["proxy"]} if options.get("proxy") else None,
            )
            
            html = response.text
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "html": html,
                "strategy": "cloudscraper",
            }
            
            # Detect protection
            if "cf-browser-verification" in html.lower() or "cloudflare" in html.lower():
                result["protection"] = "cloudflare"
            elif "datadome" in html.lower():
                result["protection"] = "datadome"
            elif "akamai" in html.lower():
                result["protection"] = "akamai"
            
            # Extract data if rules provided
            if options.get("extract") and html:
                result["extracted_data"] = self.extract_data(html, options["extract"])
            
            return result
            
        except Exception as e:
            # Fallback to basic requests
            try:
                response = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                    timeout=options.get("timeout", 30),
                )
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "html": response.text,
                    "strategy": "requests",
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": f"CloudScraper: {e}, Requests: {fallback_error}",
                }
    
    def extract_data(self, html: str, rules: dict) -> dict:
        """Extract data from HTML using CSS selectors."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            extracted = {}
            for key, selector in rules.items():
                elements = soup.select(selector)
                extracted[key] = [el.get_text(strip=True) for el in elements]
            
            return extracted
        except Exception:
            return {}
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        return
