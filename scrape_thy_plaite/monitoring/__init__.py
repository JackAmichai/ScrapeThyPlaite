"""
Real-time Monitoring Dashboard - WebSocket-based live monitoring.

Competitive Edge: Real-time visibility into scraping operations.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

from loguru import logger


@dataclass
class ScrapingMetrics:
    """Real-time scraping metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    bytes_downloaded: int = 0
    pages_per_minute: float = 0.0
    avg_response_time_ms: float = 0.0
    active_workers: int = 0
    queue_size: int = 0
    protection_blocks: int = 0
    captchas_solved: int = 0
    
    # Per-protection breakdown
    cloudflare_bypasses: int = 0
    datadome_bypasses: int = 0
    akamai_bypasses: int = 0
    other_bypasses: int = 0


@dataclass
class RequestLog:
    """Individual request log entry."""
    timestamp: float
    url: str
    status_code: int
    response_time_ms: float
    protection_detected: Optional[str]
    bypass_strategy: Optional[str]
    success: bool
    error: Optional[str]
    worker_id: str


class MetricsCollector:
    """
    Collects and aggregates scraping metrics.
    
    Thread-safe metrics collection with rolling windows.
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self._metrics = ScrapingMetrics()
        self._request_log: deque = deque(maxlen=window_size)
        self._response_times: deque = deque(maxlen=window_size)
        self._minute_requests: deque = deque(maxlen=60)
        self._last_minute_check = time.time()
        self._lock = None
    
    async def _init_lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def record_request(
        self,
        url: str,
        status_code: int,
        response_time_ms: float,
        success: bool,
        protection_detected: Optional[str] = None,
        bypass_strategy: Optional[str] = None,
        error: Optional[str] = None,
        worker_id: str = "default",
        bytes_downloaded: int = 0,
    ):
        """Record a completed request."""
        await self._init_lock()
        
        async with self._lock:
            log = RequestLog(
                timestamp=time.time(),
                url=url,
                status_code=status_code,
                response_time_ms=response_time_ms,
                protection_detected=protection_detected,
                bypass_strategy=bypass_strategy,
                success=success,
                error=error,
                worker_id=worker_id,
            )
            
            self._request_log.append(log)
            self._response_times.append(response_time_ms)
            
            # Update metrics
            self._metrics.total_requests += 1
            self._metrics.bytes_downloaded += bytes_downloaded
            
            if success:
                self._metrics.successful_requests += 1
            else:
                self._metrics.failed_requests += 1
            
            # Track protection bypasses
            if protection_detected:
                if "cloudflare" in protection_detected.lower():
                    self._metrics.cloudflare_bypasses += 1
                elif "datadome" in protection_detected.lower():
                    self._metrics.datadome_bypasses += 1
                elif "akamai" in protection_detected.lower():
                    self._metrics.akamai_bypasses += 1
                else:
                    self._metrics.other_bypasses += 1
            
            # Calculate rolling averages
            self._metrics.avg_response_time_ms = (
                sum(self._response_times) / len(self._response_times)
            )
            
            # Update requests per minute
            self._update_rpm()
    
    def _update_rpm(self):
        """Update requests per minute calculation."""
        now = time.time()
        
        # Add current count to minute window
        if now - self._last_minute_check >= 1:
            self._minute_requests.append(
                self._metrics.total_requests
            )
            self._last_minute_check = now
        
        # Calculate RPM from last 60 seconds
        if len(self._minute_requests) >= 2:
            diff = self._minute_requests[-1] - self._minute_requests[0]
            seconds = min(60, len(self._minute_requests))
            self._metrics.pages_per_minute = (diff / seconds) * 60
    
    async def record_captcha_solved(self):
        """Record a solved CAPTCHA."""
        await self._init_lock()
        async with self._lock:
            self._metrics.captchas_solved += 1
    
    async def record_protection_block(self):
        """Record a protection block."""
        await self._init_lock()
        async with self._lock:
            self._metrics.protection_blocks += 1
    
    async def update_workers(self, count: int):
        """Update active worker count."""
        await self._init_lock()
        async with self._lock:
            self._metrics.active_workers = count
    
    async def update_queue_size(self, size: int):
        """Update queue size."""
        await self._init_lock()
        async with self._lock:
            self._metrics.queue_size = size
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return asdict(self._metrics)
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request logs."""
        logs = list(self._request_log)[-limit:]
        return [asdict(log) for log in logs]
    
    def get_success_rate(self) -> float:
        """Get current success rate."""
        if self._metrics.total_requests == 0:
            return 0.0
        return self._metrics.successful_requests / self._metrics.total_requests


class MonitoringServer:
    """
    WebSocket server for real-time monitoring.
    
    Provides:
    - Real-time metrics streaming
    - Request log streaming
    - Alert notifications
    - Dashboard data endpoint
    """
    
    def __init__(
        self,
        collector: MetricsCollector,
        host: str = "0.0.0.0",
        port: int = 8765,
    ):
        self.collector = collector
        self.host = host
        self.port = port
        self._clients: Set = set()
        self._running = False
    
    async def start(self):
        """Start the WebSocket server."""
        try:
            import websockets
        except ImportError:
            logger.error("Install websockets: pip install websockets")
            return
        
        self._running = True
        
        async def handler(websocket, path):
            self._clients.add(websocket)
            try:
                async for message in websocket:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
            finally:
                self._clients.remove(websocket)
        
        server = await websockets.serve(handler, self.host, self.port)
        logger.info(f"Monitoring server started on ws://{self.host}:{self.port}")
        
        # Start broadcast loop
        asyncio.create_task(self._broadcast_loop())
        
        await server.wait_closed()
    
    async def _handle_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "get_metrics":
            await websocket.send(json.dumps({
                "type": "metrics",
                "data": self.collector.get_metrics(),
            }))
        
        elif msg_type == "get_requests":
            limit = data.get("limit", 100)
            await websocket.send(json.dumps({
                "type": "requests",
                "data": self.collector.get_recent_requests(limit),
            }))
        
        elif msg_type == "subscribe":
            # Client is already subscribed by being connected
            await websocket.send(json.dumps({
                "type": "subscribed",
                "message": "Subscribed to real-time updates",
            }))
    
    async def _broadcast_loop(self):
        """Broadcast metrics to all connected clients."""
        while self._running:
            if self._clients:
                metrics = {
                    "type": "metrics_update",
                    "timestamp": time.time(),
                    "data": self.collector.get_metrics(),
                }
                
                # Broadcast to all clients
                disconnected = set()
                for client in self._clients:
                    try:
                        await client.send(json.dumps(metrics))
                    except Exception:
                        disconnected.add(client)
                
                self._clients -= disconnected
            
            await asyncio.sleep(1)  # Update every second
    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast an alert to all clients."""
        message = {
            "type": "alert",
            "timestamp": time.time(),
            "data": alert,
        }
        
        for client in self._clients:
            try:
                await client.send(json.dumps(message))
            except Exception:
                pass
    
    def stop(self):
        """Stop the server."""
        self._running = False


# HTML Dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ScrapeThyPlaite - Live Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a; color: #e2e8f0; padding: 20px;
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #38bdf8; font-size: 2.5em; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .card {
            background: #1e293b; border-radius: 12px; padding: 20px;
            border: 1px solid #334155;
        }
        .card h3 { color: #94a3b8; font-size: 0.9em; margin-bottom: 10px; }
        .card .value { font-size: 2.5em; font-weight: bold; color: #38bdf8; }
        .card.success .value { color: #4ade80; }
        .card.warning .value { color: #fbbf24; }
        .card.error .value { color: #f87171; }
        .chart-container { margin-top: 30px; background: #1e293b; border-radius: 12px; padding: 20px; }
        .logs { margin-top: 30px; background: #1e293b; border-radius: 12px; padding: 20px; max-height: 400px; overflow-y: auto; }
        .log-entry { padding: 10px; border-bottom: 1px solid #334155; font-family: monospace; font-size: 0.85em; }
        .log-entry.success { border-left: 3px solid #4ade80; }
        .log-entry.error { border-left: 3px solid #f87171; }
        .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
        .status-dot.online { background: #4ade80; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ ScrapeThyPlaite</h1>
        <p><span class="status-dot online"></span>Live Dashboard</p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>TOTAL REQUESTS</h3>
            <div class="value" id="total-requests">0</div>
        </div>
        <div class="card success">
            <h3>SUCCESS RATE</h3>
            <div class="value" id="success-rate">0%</div>
        </div>
        <div class="card">
            <h3>PAGES/MIN</h3>
            <div class="value" id="pages-per-minute">0</div>
        </div>
        <div class="card">
            <h3>AVG RESPONSE TIME</h3>
            <div class="value" id="avg-response">0ms</div>
        </div>
        <div class="card">
            <h3>ACTIVE WORKERS</h3>
            <div class="value" id="active-workers">0</div>
        </div>
        <div class="card">
            <h3>QUEUE SIZE</h3>
            <div class="value" id="queue-size">0</div>
        </div>
        <div class="card warning">
            <h3>PROTECTION BLOCKS</h3>
            <div class="value" id="protection-blocks">0</div>
        </div>
        <div class="card">
            <h3>CAPTCHAS SOLVED</h3>
            <div class="value" id="captchas-solved">0</div>
        </div>
    </div>
    
    <div class="chart-container">
        <canvas id="chart"></canvas>
    </div>
    
    <div class="logs">
        <h3 style="color: #94a3b8; margin-bottom: 15px;">Recent Requests</h3>
        <div id="log-entries"></div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:8765');
        const chartData = { labels: [], success: [], failed: [] };
        let chart;
        
        ws.onopen = () => {
            console.log('Connected to monitoring server');
            ws.send(JSON.stringify({ type: 'subscribe' }));
        };
        
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'metrics_update') {
                updateDashboard(msg.data);
            }
        };
        
        function updateDashboard(metrics) {
            document.getElementById('total-requests').textContent = metrics.total_requests.toLocaleString();
            document.getElementById('success-rate').textContent = 
                ((metrics.successful_requests / Math.max(1, metrics.total_requests)) * 100).toFixed(1) + '%';
            document.getElementById('pages-per-minute').textContent = metrics.pages_per_minute.toFixed(1);
            document.getElementById('avg-response').textContent = metrics.avg_response_time_ms.toFixed(0) + 'ms';
            document.getElementById('active-workers').textContent = metrics.active_workers;
            document.getElementById('queue-size').textContent = metrics.queue_size;
            document.getElementById('protection-blocks').textContent = metrics.protection_blocks;
            document.getElementById('captchas-solved').textContent = metrics.captchas_solved;
            
            // Update chart
            const now = new Date().toLocaleTimeString();
            chartData.labels.push(now);
            chartData.success.push(metrics.successful_requests);
            chartData.failed.push(metrics.failed_requests);
            
            if (chartData.labels.length > 60) {
                chartData.labels.shift();
                chartData.success.shift();
                chartData.failed.shift();
            }
            
            if (chart) chart.update();
        }
        
        // Initialize chart
        const ctx = document.getElementById('chart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    { label: 'Successful', data: chartData.success, borderColor: '#4ade80', tension: 0.3 },
                    { label: 'Failed', data: chartData.failed, borderColor: '#f87171', tension: 0.3 }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    x: { ticks: { color: '#64748b' } },
                    y: { ticks: { color: '#64748b' } }
                }
            }
        });
    </script>
</body>
</html>
"""


# Exports
__all__ = [
    "ScrapingMetrics",
    "RequestLog",
    "MetricsCollector",
    "MonitoringServer",
    "DASHBOARD_HTML",
]
