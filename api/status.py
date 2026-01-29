"""
Vercel Serverless API - Job Status Endpoint
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import parse_qs, urlparse


# In-memory job storage (shared with batch.py)
JOBS_STORE = {}


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
    def do_GET(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # Verify API key
        if not verify_api_key(dict(self.headers)):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid API key"}).encode())
            return
        
        # Extract job_id from URL
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip('/').split('/')
        
        # Try to get job_id from path or query params
        job_id = None
        if len(path_parts) >= 3 and path_parts[0] == 'api' and path_parts[1] == 'status':
            job_id = path_parts[2]
        else:
            query_params = parse_qs(parsed.query)
            job_id = query_params.get('job_id', [None])[0]
        
        if not job_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Job ID is required"}).encode())
            return
        
        # Get job from storage
        job = get_job(job_id)
        
        if not job:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Job not found",
                "job_id": job_id,
            }).encode())
            return
        
        # Calculate progress
        progress = job["completed"] / max(1, job["total"])
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "progress": round(progress, 2),
            "completed": job["completed"],
            "total": job["total"],
            "created_at": job["created_at"],
            "results": job.get("results") if job["status"] == "completed" else None,
            "error": job.get("error"),
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
        return
