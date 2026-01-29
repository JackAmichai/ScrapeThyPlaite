"""
FastAPI Server - Production-ready API for ScrapeThyPlaite.

Provides REST API endpoints for scraping operations.
"""

import os
import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from loguru import logger

# Initialize FastAPI app
app = FastAPI(
    title="ScrapeThyPlaite API",
    description="Advanced Web Scraping API with Protection Bypass",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Request/Response Models ============

class ScrapeRequest(BaseModel):
    """Request model for scraping."""
    url: HttpUrl = Field(..., description="URL to scrape")
    engine: Optional[str] = Field(
        None,
        description="Scraping engine (auto, selenium, playwright, httpx, etc.)"
    )
    wait_for: Optional[str] = Field(
        None,
        description="CSS selector to wait for before scraping"
    )
    extract: Optional[Dict[str, str]] = Field(
        None,
        description="Data extraction rules (CSS selectors or XPath)"
    )
    javascript: bool = Field(
        False,
        description="Whether to execute JavaScript"
    )
    proxy: Optional[str] = Field(
        None,
        description="Proxy URL to use"
    )
    headers: Optional[Dict[str, str]] = Field(
        None,
        description="Custom headers"
    )
    timeout: int = Field(
        30,
        description="Request timeout in seconds"
    )
    bypass_protection: bool = Field(
        True,
        description="Attempt to bypass anti-bot protection"
    )


class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping."""
    urls: List[HttpUrl] = Field(..., description="URLs to scrape")
    engine: Optional[str] = None
    concurrency: int = Field(5, ge=1, le=50)
    extract: Optional[Dict[str, str]] = None
    javascript: bool = False
    proxy: Optional[str] = None
    timeout: int = 30


class ScrapeResponse(BaseModel):
    """Response model for scraping."""
    success: bool
    url: str
    status_code: Optional[int] = None
    html: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    protection_detected: Optional[str] = None
    bypass_strategy: Optional[str] = None
    response_time_ms: float
    error: Optional[str] = None


class JobResponse(BaseModel):
    """Response model for async jobs."""
    job_id: str
    status: str
    created_at: str
    urls_count: int


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    progress: float
    completed: int
    total: int
    results: Optional[List[ScrapeResponse]] = None
    error: Optional[str] = None


# ============ In-memory Job Storage ============

jobs: Dict[str, Dict[str, Any]] = {}


def generate_job_id() -> str:
    """Generate unique job ID."""
    return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:12]


# ============ Authentication ============

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key if configured."""
    required_key = os.getenv("SCRAPER_API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ============ API Endpoints ============

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "ScrapeThyPlaite API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Scrape a single URL.
    
    Automatically detects and bypasses protection systems.
    """
    start_time = time.time()
    
    try:
        # Import scraper (lazy import for serverless)
        from scrape_thy_plaite import UltimateScraper
        
        scraper = UltimateScraper()
        
        # Configure options
        options = {
            "headers": request.headers or {},
            "timeout": request.timeout,
        }
        
        if request.proxy:
            options["proxy"] = request.proxy
        
        # Perform scraping
        result = await scraper.scrape(str(request.url), **options)
        
        response_time = (time.time() - start_time) * 1000
        
        # Extract data if rules provided
        extracted = None
        if request.extract and result.get("html"):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result["html"], "html.parser")
            extracted = {}
            for key, selector in request.extract.items():
                elements = soup.select(selector)
                extracted[key] = [el.get_text(strip=True) for el in elements]
        
        return ScrapeResponse(
            success=result.get("success", False),
            url=str(request.url),
            status_code=result.get("status_code"),
            html=result.get("html") if not request.extract else None,
            extracted_data=extracted,
            protection_detected=result.get("protection"),
            bypass_strategy=result.get("strategy"),
            response_time_ms=response_time,
        )
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        response_time = (time.time() - start_time) * 1000
        return ScrapeResponse(
            success=False,
            url=str(request.url),
            response_time_ms=response_time,
            error=str(e),
        )


@app.post("/scrape/batch", response_model=JobResponse)
async def batch_scrape(
    request: BatchScrapeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    """
    Start a batch scraping job.
    
    Returns a job ID to track progress.
    """
    job_id = generate_job_id()
    
    jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.utcnow().isoformat(),
        "urls": [str(url) for url in request.urls],
        "completed": 0,
        "total": len(request.urls),
        "results": [],
        "error": None,
    }
    
    # Start background processing
    background_tasks.add_task(
        process_batch_job,
        job_id,
        request,
    )
    
    return JobResponse(
        job_id=job_id,
        status="processing",
        created_at=jobs[job_id]["created_at"],
        urls_count=len(request.urls),
    )


async def process_batch_job(job_id: str, request: BatchScrapeRequest):
    """Process batch scraping job in background."""
    try:
        from scrape_thy_plaite import UltimateScraper
        
        scraper = UltimateScraper()
        urls = [str(url) for url in request.urls]
        
        for i, url in enumerate(urls):
            try:
                start_time = time.time()
                result = await scraper.scrape(url, timeout=request.timeout)
                response_time = (time.time() - start_time) * 1000
                
                jobs[job_id]["results"].append(ScrapeResponse(
                    success=result.get("success", False),
                    url=url,
                    status_code=result.get("status_code"),
                    html=result.get("html")[:5000] if result.get("html") else None,
                    protection_detected=result.get("protection"),
                    response_time_ms=response_time,
                ))
            except Exception as e:
                jobs[job_id]["results"].append(ScrapeResponse(
                    success=False,
                    url=url,
                    response_time_ms=0,
                    error=str(e),
                ))
            
            jobs[job_id]["completed"] = i + 1
            
            # Small delay to avoid overwhelming
            await asyncio.sleep(0.1)
        
        jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        logger.error(f"Batch job {job_id} failed: {e}")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get the status of a batch scraping job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    progress = job["completed"] / max(1, job["total"])
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=progress,
        completed=job["completed"],
        total=job["total"],
        results=job["results"] if job["status"] == "completed" else None,
        error=job["error"],
    )


@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Delete a completed job and its results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs[job_id]
    return {"message": "Job deleted"}


@app.get("/engines")
async def list_engines():
    """List available scraping engines."""
    return {
        "engines": [
            {"id": "auto", "name": "Auto Select", "description": "Automatically selects best engine"},
            {"id": "httpx", "name": "HTTPX", "description": "Fast async HTTP client"},
            {"id": "cloudscraper", "name": "CloudScraper", "description": "Cloudflare bypass"},
            {"id": "selenium", "name": "Selenium", "description": "Full browser automation"},
            {"id": "playwright", "name": "Playwright", "description": "Modern browser automation"},
            {"id": "undetected", "name": "Undetected Chrome", "description": "Stealth Chrome"},
            {"id": "tls", "name": "TLS Fingerprint", "description": "Custom TLS fingerprinting"},
            {"id": "drissionpage", "name": "DrissionPage", "description": "Hybrid automation"},
        ]
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
