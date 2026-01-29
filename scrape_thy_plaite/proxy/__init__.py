"""
Proxy Management Module - Handle proxy rotation and health checking.
"""

import asyncio
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from loguru import logger

from scrape_thy_plaite.core.config import ProxyConfig, ProxyRotationStrategy
from scrape_thy_plaite.core.exceptions import ProxyError


class ProxyProtocol(str, Enum):
    """Supported proxy protocols."""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class Proxy:
    """Proxy representation with metadata."""
    url: str
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    host: str = ""
    port: int = 0
    
    # Stats
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    is_healthy: bool = True
    
    def __post_init__(self):
        """Parse proxy URL."""
        self._parse_url()
    
    def _parse_url(self):
        """Parse proxy URL into components."""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.url)
        self.protocol = ProxyProtocol(parsed.scheme) if parsed.scheme else ProxyProtocol.HTTP
        self.host = parsed.hostname or ""
        self.port = parsed.port or 8080
        self.username = parsed.username
        self.password = parsed.password
    
    @property
    def formatted_url(self) -> str:
        """Get formatted proxy URL."""
        if self.username and self.password:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests
    
    def record_success(self, response_time: float):
        """Record a successful request."""
        self.success_count += 1
        self.total_requests += 1
        self.last_used = datetime.now()
        
        # Update average response time
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time + response_time) / 2
    
    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.total_requests += 1
        self.last_used = datetime.now()


class ProxyManager:
    """
    Manages proxy pool with rotation and health checking.
    
    Features:
    - Multiple rotation strategies
    - Automatic health checking
    - Failure tracking and blacklisting
    - Session stickiness support
    - Load balancing
    
    Example:
        manager = ProxyManager(
            proxies=[
                "http://user:pass@proxy1.com:8080",
                "socks5://proxy2.com:1080",
            ],
            rotation_strategy="round_robin",
            health_check=True
        )
        
        proxy = await manager.get_proxy()
        # Use proxy...
        await manager.report_result(proxy, success=True, response_time=0.5)
    """
    
    def __init__(self, config: Optional[ProxyConfig] = None, **kwargs):
        """
        Initialize proxy manager.
        
        Args:
            config: ProxyConfig object
            proxies: List of proxy URLs (alternative to config)
            rotation_strategy: Strategy for proxy selection
            health_check: Whether to perform health checks
        """
        self.config = config or ProxyConfig()
        
        # Override with kwargs if provided
        if "proxies" in kwargs:
            self.config.proxies = kwargs["proxies"]
        if "rotation_strategy" in kwargs:
            self.config.rotation_strategy = ProxyRotationStrategy(kwargs["rotation_strategy"])
        if "health_check" in kwargs:
            self.config.health_check = kwargs["health_check"]
        
        # Initialize proxy pool
        self._proxies: List[Proxy] = []
        self._current_index = 0
        self._sticky_sessions: Dict[str, Proxy] = {}
        self._lock = asyncio.Lock()
        
        # Load proxies
        for proxy_url in self.config.proxies:
            self._proxies.append(Proxy(url=proxy_url))
        
        logger.info(f"ProxyManager initialized with {len(self._proxies)} proxies")
    
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[Proxy]:
        """
        Get a proxy based on rotation strategy.
        
        Args:
            session_id: Optional session ID for sticky sessions
            
        Returns:
            Proxy object or None if no proxies available
        """
        if not self._proxies:
            return None
        
        async with self._lock:
            # Check for sticky session
            if session_id and session_id in self._sticky_sessions:
                proxy = self._sticky_sessions[session_id]
                if proxy.is_healthy:
                    return proxy
            
            # Get healthy proxies
            healthy_proxies = [p for p in self._proxies if p.is_healthy]
            if not healthy_proxies:
                logger.warning("No healthy proxies available, using all proxies")
                healthy_proxies = self._proxies
            
            # Select proxy based on strategy
            proxy = self._select_proxy(healthy_proxies)
            
            # Store sticky session
            if session_id and self.config.rotation_strategy == ProxyRotationStrategy.STICKY:
                self._sticky_sessions[session_id] = proxy
            
            return proxy
    
    def _select_proxy(self, proxies: List[Proxy]) -> Proxy:
        """Select proxy based on rotation strategy."""
        strategy = self.config.rotation_strategy
        
        if strategy == ProxyRotationStrategy.ROUND_ROBIN:
            proxy = proxies[self._current_index % len(proxies)]
            self._current_index += 1
            return proxy
        
        elif strategy == ProxyRotationStrategy.RANDOM:
            return random.choice(proxies)
        
        elif strategy == ProxyRotationStrategy.LEAST_USED:
            return min(proxies, key=lambda p: p.total_requests)
        
        elif strategy == ProxyRotationStrategy.STICKY:
            # For sticky, just return first available
            return proxies[0]
        
        return random.choice(proxies)
    
    async def report_result(
        self, 
        proxy: Proxy, 
        success: bool, 
        response_time: float = 0.0
    ) -> None:
        """
        Report the result of using a proxy.
        
        Args:
            proxy: The proxy that was used
            success: Whether the request succeeded
            response_time: Response time in seconds
        """
        async with self._lock:
            if success:
                proxy.record_success(response_time)
            else:
                proxy.record_failure()
                
                # Check if proxy should be marked unhealthy
                if proxy.failure_count >= self.config.max_failures:
                    proxy.is_healthy = False
                    logger.warning(f"Proxy marked unhealthy: {proxy.host}:{proxy.port}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all proxies.
        
        Returns:
            Dict mapping proxy URLs to health status
        """
        results = {}
        
        async def check_proxy(proxy: Proxy):
            try:
                import httpx
                async with httpx.AsyncClient(
                    proxy=proxy.formatted_url,
                    timeout=10
                ) as client:
                    response = await client.get(self.config.health_check_url)
                    success = response.status_code == 200
                    proxy.is_healthy = success
                    proxy.last_checked = datetime.now()
                    results[proxy.url] = success
            except Exception as e:
                logger.warning(f"Health check failed for {proxy.host}: {e}")
                proxy.is_healthy = False
                proxy.last_checked = datetime.now()
                results[proxy.url] = False
        
        await asyncio.gather(*[check_proxy(p) for p in self._proxies])
        
        healthy_count = sum(1 for v in results.values() if v)
        logger.info(f"Health check complete: {healthy_count}/{len(self._proxies)} healthy")
        
        return results
    
    def add_proxy(self, proxy_url: str) -> None:
        """Add a new proxy to the pool."""
        self._proxies.append(Proxy(url=proxy_url))
        logger.info(f"Added proxy: {proxy_url}")
    
    def remove_proxy(self, proxy_url: str) -> bool:
        """Remove a proxy from the pool."""
        for i, proxy in enumerate(self._proxies):
            if proxy.url == proxy_url:
                self._proxies.pop(i)
                logger.info(f"Removed proxy: {proxy_url}")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        return {
            "total_proxies": len(self._proxies),
            "healthy_proxies": sum(1 for p in self._proxies if p.is_healthy),
            "total_requests": sum(p.total_requests for p in self._proxies),
            "total_successes": sum(p.success_count for p in self._proxies),
            "total_failures": sum(p.failure_count for p in self._proxies),
            "avg_success_rate": sum(p.success_rate for p in self._proxies) / len(self._proxies) if self._proxies else 0,
            "proxies": [
                {
                    "url": p.url,
                    "is_healthy": p.is_healthy,
                    "success_rate": p.success_rate,
                    "total_requests": p.total_requests,
                    "avg_response_time": p.avg_response_time,
                }
                for p in self._proxies
            ]
        }
    
    def clear_sticky_sessions(self) -> None:
        """Clear all sticky sessions."""
        self._sticky_sessions.clear()
        logger.info("Cleared all sticky sessions")
    
    async def reset_all(self) -> None:
        """Reset all proxy statistics and health status."""
        async with self._lock:
            for proxy in self._proxies:
                proxy.success_count = 0
                proxy.failure_count = 0
                proxy.total_requests = 0
                proxy.avg_response_time = 0.0
                proxy.is_healthy = True
            self._sticky_sessions.clear()
            self._current_index = 0
        logger.info("Reset all proxy statistics")


class ProxyProviders:
    """
    Integration with popular proxy providers.
    
    Supported providers:
    - Bright Data (formerly Luminati)
    - Oxylabs
    - Smartproxy
    - ProxyMesh
    """
    
    @staticmethod
    def bright_data(
        username: str,
        password: str,
        zone: str = "residential",
        country: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Generate Bright Data proxy URL.
        
        Args:
            username: Bright Data username
            password: Bright Data password
            zone: Zone name (residential, datacenter, etc.)
            country: Target country code (e.g., "us", "uk")
            session_id: Session ID for sticky sessions
        """
        host = "brd.superproxy.io"
        port = 22225
        
        user = f"{username}-zone-{zone}"
        if country:
            user += f"-country-{country}"
        if session_id:
            user += f"-session-{session_id}"
        
        return f"http://{user}:{password}@{host}:{port}"
    
    @staticmethod
    def oxylabs(
        username: str,
        password: str,
        country: Optional[str] = None,
        city: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Generate Oxylabs proxy URL."""
        host = "pr.oxylabs.io"
        port = 7777
        
        user = username
        if country:
            user += f"-cc-{country}"
        if city:
            user += f"-city-{city}"
        if session_id:
            user += f"-sessid-{session_id}"
        
        return f"http://{user}:{password}@{host}:{port}"
    
    @staticmethod
    def smartproxy(
        username: str,
        password: str,
        country: Optional[str] = None,
        session_type: str = "rotating"
    ) -> str:
        """Generate Smartproxy proxy URL."""
        host = "gate.smartproxy.com"
        port = 7000
        
        user = username
        if country:
            user = f"user-{username}-country-{country}"
        if session_type == "sticky":
            user += "-session-" + str(random.randint(10000, 99999))
        
        return f"http://{user}:{password}@{host}:{port}"
