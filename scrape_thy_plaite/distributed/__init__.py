"""
Distributed Scraping System - Redis-based job queue for massive scale.

Competitive Edge: Handle millions of URLs with distributed workers.
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

from loguru import logger


class JobStatus(str, Enum):
    """Job status states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class ScrapeJob:
    """A scraping job."""
    id: str
    url: str
    config: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    priority: int = JobPriority.NORMAL
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    worker_id: Optional[str] = None
    webhook_url: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapeJob":
        data["status"] = JobStatus(data["status"])
        return cls(**data)


class JobQueue:
    """
    Redis-based distributed job queue.
    
    Features:
    - Priority queues
    - Job deduplication
    - Automatic retries
    - Dead letter queue
    - Job scheduling
    - Real-time progress
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "scrape_jobs",
        max_workers: int = 10,
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.max_workers = max_workers
        self._redis = None
        self._pubsub = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(self.redis_url)
            self._pubsub = self._redis.pubsub()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except ImportError:
            raise ImportError("Install redis: pip install redis")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
    
    async def enqueue(
        self,
        url: str,
        config: Dict[str, Any] = None,
        priority: JobPriority = JobPriority.NORMAL,
        webhook_url: Optional[str] = None,
        tags: List[str] = None,
        dedupe: bool = True,
    ) -> ScrapeJob:
        """
        Add a job to the queue.
        
        Args:
            url: URL to scrape
            config: Scraper configuration
            priority: Job priority
            webhook_url: URL to call when job completes
            tags: Tags for filtering/grouping
            dedupe: Skip if URL already in queue
        """
        # Check for duplicates
        if dedupe:
            existing = await self._redis.get(f"url_hash:{hash(url)}")
            if existing:
                logger.info(f"Duplicate URL skipped: {url}")
                return ScrapeJob.from_dict(json.loads(existing))
        
        job = ScrapeJob(
            id=str(uuid.uuid4()),
            url=url,
            config=config or {},
            priority=priority,
            webhook_url=webhook_url,
            tags=tags or [],
        )
        
        # Store job data
        await self._redis.set(
            f"job:{job.id}",
            json.dumps(job.to_dict()),
            ex=86400 * 7  # 7 day TTL
        )
        
        # Add to priority queue
        await self._redis.zadd(
            f"{self.queue_name}:pending",
            {job.id: priority}
        )
        
        # Store URL hash for deduplication
        if dedupe:
            await self._redis.set(
                f"url_hash:{hash(url)}",
                json.dumps(job.to_dict()),
                ex=3600  # 1 hour dedupe window
            )
        
        # Publish event
        await self._redis.publish(
            f"{self.queue_name}:events",
            json.dumps({"event": "job_created", "job_id": job.id})
        )
        
        logger.info(f"Job enqueued: {job.id} - {url}")
        return job
    
    async def enqueue_batch(
        self,
        urls: List[str],
        config: Dict[str, Any] = None,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> List[ScrapeJob]:
        """Enqueue multiple URLs efficiently."""
        jobs = []
        pipe = self._redis.pipeline()
        
        for url in urls:
            job = ScrapeJob(
                id=str(uuid.uuid4()),
                url=url,
                config=config or {},
                priority=priority,
            )
            
            pipe.set(f"job:{job.id}", json.dumps(job.to_dict()), ex=86400 * 7)
            pipe.zadd(f"{self.queue_name}:pending", {job.id: priority})
            jobs.append(job)
        
        await pipe.execute()
        logger.info(f"Batch enqueued: {len(jobs)} jobs")
        return jobs
    
    async def dequeue(self, worker_id: str) -> Optional[ScrapeJob]:
        """Get the next job from the queue."""
        # Get highest priority job
        result = await self._redis.zpopmax(f"{self.queue_name}:pending")
        
        if not result:
            return None
        
        job_id, _ = result[0]
        job_data = await self._redis.get(f"job:{job_id}")
        
        if not job_data:
            return None
        
        job = ScrapeJob.from_dict(json.loads(job_data))
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        job.worker_id = worker_id
        
        # Update job
        await self._redis.set(f"job:{job.id}", json.dumps(job.to_dict()))
        
        # Add to running set
        await self._redis.sadd(f"{self.queue_name}:running", job.id)
        
        return job
    
    async def complete(
        self,
        job: ScrapeJob,
        result: Dict[str, Any],
    ):
        """Mark job as completed."""
        job.status = JobStatus.COMPLETED
        job.completed_at = time.time()
        job.result = result
        
        # Update job
        await self._redis.set(f"job:{job.id}", json.dumps(job.to_dict()))
        
        # Remove from running
        await self._redis.srem(f"{self.queue_name}:running", job.id)
        
        # Add to completed
        await self._redis.zadd(
            f"{self.queue_name}:completed",
            {job.id: job.completed_at}
        )
        
        # Call webhook if configured
        if job.webhook_url:
            await self._call_webhook(job)
        
        # Publish event
        await self._redis.publish(
            f"{self.queue_name}:events",
            json.dumps({"event": "job_completed", "job_id": job.id})
        )
        
        logger.info(f"Job completed: {job.id}")
    
    async def fail(
        self,
        job: ScrapeJob,
        error: str,
        retry: bool = True,
    ):
        """Mark job as failed with optional retry."""
        job.error = error
        job.retries += 1
        
        if retry and job.retries < job.max_retries:
            job.status = JobStatus.RETRYING
            
            # Re-enqueue with lower priority
            await self._redis.zadd(
                f"{self.queue_name}:pending",
                {job.id: job.priority - 1}
            )
            logger.warning(f"Job retry {job.retries}/{job.max_retries}: {job.id}")
        else:
            job.status = JobStatus.FAILED
            job.completed_at = time.time()
            
            # Add to dead letter queue
            await self._redis.zadd(
                f"{self.queue_name}:failed",
                {job.id: job.completed_at}
            )
            logger.error(f"Job failed: {job.id} - {error}")
        
        # Update job
        await self._redis.set(f"job:{job.id}", json.dumps(job.to_dict()))
        
        # Remove from running
        await self._redis.srem(f"{self.queue_name}:running", job.id)
        
        # Call webhook
        if job.webhook_url:
            await self._call_webhook(job)
    
    async def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Get job by ID."""
        data = await self._redis.get(f"job:{job_id}")
        if data:
            return ScrapeJob.from_dict(json.loads(data))
        return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending = await self._redis.zcard(f"{self.queue_name}:pending")
        running = await self._redis.scard(f"{self.queue_name}:running")
        completed = await self._redis.zcard(f"{self.queue_name}:completed")
        failed = await self._redis.zcard(f"{self.queue_name}:failed")
        
        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "total": pending + running + completed + failed,
        }
    
    async def _call_webhook(self, job: ScrapeJob):
        """Call webhook URL with job result."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    job.webhook_url,
                    json=job.to_dict(),
                    timeout=30,
                )
        except Exception as e:
            logger.error(f"Webhook failed: {e}")


class Worker:
    """
    Distributed scraping worker.
    
    Processes jobs from the queue using any scraping engine.
    """
    
    def __init__(
        self,
        queue: JobQueue,
        worker_id: str = None,
        scraper_factory: Callable = None,
    ):
        self.queue = queue
        self.worker_id = worker_id or str(uuid.uuid4())[:8]
        self.scraper_factory = scraper_factory
        self._running = False
        self._current_job: Optional[ScrapeJob] = None
    
    async def start(self):
        """Start processing jobs."""
        from scrape_thy_plaite.engines import UltimateScraper
        
        self._running = True
        logger.info(f"Worker {self.worker_id} started")
        
        while self._running:
            job = await self.queue.dequeue(self.worker_id)
            
            if not job:
                await asyncio.sleep(1)
                continue
            
            self._current_job = job
            
            try:
                # Create scraper
                if self.scraper_factory:
                    scraper = self.scraper_factory(job.config)
                else:
                    scraper = UltimateScraper()
                
                await scraper.initialize()
                
                # Scrape
                result = await scraper.scrape(job.url, **job.config)
                
                await scraper.close()
                
                if result.get("success"):
                    await self.queue.complete(job, result)
                else:
                    await self.queue.fail(job, result.get("error", "Unknown error"))
                    
            except Exception as e:
                logger.exception(f"Worker error: {e}")
                await self.queue.fail(job, str(e))
            
            self._current_job = None
    
    async def stop(self):
        """Stop the worker gracefully."""
        self._running = False
        logger.info(f"Worker {self.worker_id} stopped")


class DistributedScraper:
    """
    High-level interface for distributed scraping.
    
    Example:
        scraper = DistributedScraper(redis_url="redis://localhost:6379")
        await scraper.start_workers(num_workers=5)
        
        # Enqueue URLs
        jobs = await scraper.scrape_batch([
            "https://example1.com",
            "https://example2.com",
        ])
        
        # Wait for results
        results = await scraper.wait_for_jobs(jobs)
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "scrape_jobs",
    ):
        self.queue = JobQueue(redis_url, queue_name)
        self.workers: List[Worker] = []
        self._worker_tasks: List[asyncio.Task] = []
    
    async def connect(self):
        """Connect to Redis."""
        await self.queue.connect()
    
    async def start_workers(self, num_workers: int = 5):
        """Start worker processes."""
        for i in range(num_workers):
            worker = Worker(self.queue, f"worker-{i}")
            self.workers.append(worker)
            task = asyncio.create_task(worker.start())
            self._worker_tasks.append(task)
        
        logger.info(f"Started {num_workers} workers")
    
    async def stop_workers(self):
        """Stop all workers."""
        for worker in self.workers:
            await worker.stop()
        
        for task in self._worker_tasks:
            task.cancel()
    
    async def scrape(
        self,
        url: str,
        config: Dict[str, Any] = None,
        wait: bool = True,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Scrape a single URL."""
        job = await self.queue.enqueue(url, config)
        
        if not wait:
            return {"job_id": job.id, "status": "pending"}
        
        return await self._wait_for_job(job.id, timeout)
    
    async def scrape_batch(
        self,
        urls: List[str],
        config: Dict[str, Any] = None,
        wait: bool = False,
    ) -> List[ScrapeJob]:
        """Scrape multiple URLs."""
        return await self.queue.enqueue_batch(urls, config)
    
    async def _wait_for_job(
        self,
        job_id: str,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Wait for a job to complete."""
        start = time.time()
        
        while time.time() - start < timeout:
            job = await self.queue.get_job(job_id)
            
            if job.status == JobStatus.COMPLETED:
                return job.result
            elif job.status == JobStatus.FAILED:
                return {"error": job.error, "status": "failed"}
            
            await asyncio.sleep(0.5)
        
        return {"error": "Timeout", "status": "timeout"}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return await self.queue.get_stats()


# Exports
__all__ = [
    "JobStatus",
    "JobPriority", 
    "ScrapeJob",
    "JobQueue",
    "Worker",
    "DistributedScraper",
]
