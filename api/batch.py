"""
Vercel Serverless API - Batch Scraping Endpoint

Uses Vercel KV (Redis) for job storage in production.
Falls back to in-memory storage for development.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import time
import hashlib
from datetime import datetime


# In-memory job storage (use Vercel KV in production)
JOBS_STORE = {}


def generate_job_id() -> str:
    """Generate unique job ID."""
    return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:12]


def verify_api_key(headers):
    """Verify API key if configured."""
    required_key = os.environ.get("SCRAPER_API_KEY")
    if required_key:
        provided_key = headers.get("X-Api-Key") or headers.get("x-api-key")
        if provided_key != required_key:
            return False
    return True


def get_redis_client():
    """Get Redis client for Vercel KV."""
    redis_url = os.environ.get("REDIS_URL") or os.environ.get("KV_URL")
    if not redis_url:
        return None
    
    try:
        import redis
        return redis.from_url(redis_url)
    except Exception:
        return None


def save_job(job_id: str, job_data: dict):
    """Save job to storage."""
    redis_client = get_redis_client()
    if redis_client:
        redis_client.setex(
            f"job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps(job_data)
        )
    else:
        JOBS_STORE[job_id] = job_data


def get_job(job_id: str) -> dict:
    """Get job from storage."""
    redis_client = get_redis_client()
    if redis_client:
        data = redis_client.get(f"job:{job_id}")
        if data:
            return json.loads(data)
        return None
    else:
        return JOBS_STORE.get(job_id)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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
        
        # Validate URLs
        urls = request_data.get("urls", [])
        if not urls:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URLs array is required"}).encode())
            return
        
        if len(urls) > 100:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Maximum 100 URLs per batch"}).encode())
            return
        
        # Create job
        job_id = generate_job_id()
        job_data = {
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "urls": urls,
            "options": {
                "concurrency": request_data.get("concurrency", 5),
                "timeout": request_data.get("timeout", 30),
                "extract": request_data.get("extract"),
                "headers": request_data.get("headers", {}),
            },
            "completed": 0,
            "total": len(urls),
            "results": [],
            "error": None,
        }
        
        # For serverless, we process synchronously (limited by timeout)
        # For production scale, use Vercel Cron or external queue
        results = self.process_batch(urls, job_data["options"])
        
        job_data["completed"] = len(results)
        job_data["results"] = results
        job_data["status"] = "completed"
        
        save_job(job_id, job_data)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": job_data["created_at"],
            "urls_count": len(urls),
            "completed": job_data["completed"],
            "results": job_data["results"],
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def process_batch(self, urls: list, options: dict) -> list:
        """Process batch of URLs."""
        import requests
        
        results = []
        
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
        except ImportError:
            scraper = requests.Session()
        
        for url in urls:
            start_time = time.time()
            
            try:
                response = scraper.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        **options.get("headers", {}),
                    },
                    timeout=min(options.get("timeout", 30), 15),  # Limit per-URL timeout
                )
                
                response_time = (time.time() - start_time) * 1000
                
                result = {
                    "success": response.status_code == 200,
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "content_length": len(response.text),
                }
                
                # Extract data if rules provided
                if options.get("extract") and response.status_code == 200:
                    result["extracted_data"] = self.extract_data(
                        response.text,
                        options["extract"]
                    )
                
                results.append(result)
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results.append({
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "response_time_ms": round(response_time, 2),
                })
        
        return results
    
    def extract_data(self, html: str, rules: dict) -> dict:
        """Extract data using CSS selectors."""
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
