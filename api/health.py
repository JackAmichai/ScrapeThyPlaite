"""
Vercel Serverless API - Health Check Endpoint
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Check dependencies
        dependencies = {}
        
        # Check cloudscraper
        try:
            import cloudscraper
            dependencies["cloudscraper"] = "available"
        except ImportError:
            dependencies["cloudscraper"] = "not installed"
        
        # Check beautifulsoup
        try:
            from bs4 import BeautifulSoup
            dependencies["beautifulsoup4"] = "available"
        except ImportError:
            dependencies["beautifulsoup4"] = "not installed"
        
        # Check Redis connection
        redis_url = os.environ.get("REDIS_URL") or os.environ.get("KV_URL")
        if redis_url:
            try:
                import redis
                client = redis.from_url(redis_url)
                client.ping()
                dependencies["redis"] = "connected"
            except Exception as e:
                dependencies["redis"] = f"error: {str(e)}"
        else:
            dependencies["redis"] = "not configured"
        
        response = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "environment": os.environ.get("VERCEL_ENV", "development"),
            "region": os.environ.get("VERCEL_REGION", "unknown"),
            "dependencies": dependencies,
            "capabilities": {
                "single_scrape": True,
                "batch_scrape": True,
                "protection_bypass": True,
                "data_extraction": dependencies.get("beautifulsoup4") == "available",
                "cloudflare_bypass": dependencies.get("cloudscraper") == "available",
                "job_persistence": dependencies.get("redis") == "connected",
            }
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        return
