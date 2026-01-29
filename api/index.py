"""
Vercel Serverless API - Main Entry Point

ScrapeThyPlaite - Advanced Web Scraping API
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "name": "ScrapeThyPlaite API",
            "version": "1.0.0",
            "description": "Advanced Web Scraping API with Protection Bypass",
            "status": "operational",
            "endpoints": {
                "scrape": {
                    "path": "/api/scrape",
                    "method": "POST",
                    "description": "Scrape a single URL with automatic protection bypass"
                },
                "batch": {
                    "path": "/api/batch",
                    "method": "POST", 
                    "description": "Start a batch scraping job"
                },
                "status": {
                    "path": "/api/status/{job_id}",
                    "method": "GET",
                    "description": "Get batch job status"
                },
                "health": {
                    "path": "/api/health",
                    "method": "GET",
                    "description": "Health check endpoint"
                }
            },
            "features": [
                "Cloudflare Bypass",
                "DataDome Bypass", 
                "Akamai Bypass",
                "PerimeterX Bypass",
                "Kasada Bypass",
                "Arkose Labs Bypass",
                "CAPTCHA Solving",
                "AI-Powered Extraction",
                "Browser Fingerprint Rotation",
                "Distributed Scraping"
            ],
            "documentation": "https://github.com/JackAmichai/ScrapeThyPlaite"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        return
