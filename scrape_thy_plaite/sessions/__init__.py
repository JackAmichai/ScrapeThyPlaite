"""
Session Management - Persistent browser sessions and authentication.

Competitive Edge: Reuse authenticated sessions across runs, share cookies between workers.
"""

import json
import pickle
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import hashlib

from loguru import logger


@dataclass
class BrowserSession:
    """Represents a browser session state."""
    id: str
    domain: str
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    created_at: float
    last_used_at: float
    user_agent: str
    extra_data: Dict[str, Any]
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session is expired."""
        age_hours = (time.time() - self.last_used_at) / 3600
        return age_hours > max_age_hours


class SessionManager:
    """
    Manages persistent browser sessions.
    
    Features:
    - Save/restore cookies, localStorage, sessionStorage
    - Share sessions between workers via Redis
    - Automatic session rotation
    - Login state detection
    - Session pooling for rate limiting
    """
    
    def __init__(
        self,
        storage_path: str = "./sessions",
        redis_url: Optional[str] = None,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.redis_url = redis_url
        self._redis = None
        self._sessions: Dict[str, BrowserSession] = {}
    
    async def _init_redis(self):
        """Initialize Redis connection for distributed sessions."""
        if self.redis_url and not self._redis:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                logger.warning("Redis not available, using local storage only")
    
    def _get_session_id(self, domain: str, user_id: Optional[str] = None) -> str:
        """Generate session ID."""
        key = f"{domain}:{user_id or 'default'}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    async def save_session(
        self,
        domain: str,
        cookies: List[Dict[str, Any]],
        local_storage: Dict[str, str] = None,
        session_storage: Dict[str, str] = None,
        user_agent: str = None,
        user_id: Optional[str] = None,
        extra_data: Dict[str, Any] = None,
    ) -> str:
        """
        Save browser session state.
        
        Args:
            domain: Website domain
            cookies: Browser cookies
            local_storage: localStorage data
            session_storage: sessionStorage data
            user_agent: Browser user agent
            user_id: Optional user identifier
            extra_data: Any additional data to store
            
        Returns:
            Session ID
        """
        session_id = self._get_session_id(domain, user_id)
        
        session = BrowserSession(
            id=session_id,
            domain=domain,
            cookies=cookies,
            local_storage=local_storage or {},
            session_storage=session_storage or {},
            created_at=time.time(),
            last_used_at=time.time(),
            user_agent=user_agent or "",
            extra_data=extra_data or {},
        )
        
        # Save locally
        self._sessions[session_id] = session
        session_file = self.storage_path / f"{session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump({
                "id": session.id,
                "domain": session.domain,
                "cookies": session.cookies,
                "local_storage": session.local_storage,
                "session_storage": session.session_storage,
                "created_at": session.created_at,
                "last_used_at": session.last_used_at,
                "user_agent": session.user_agent,
                "extra_data": session.extra_data,
            }, f, indent=2)
        
        # Save to Redis for distributed access
        await self._init_redis()
        if self._redis:
            await self._redis.set(
                f"session:{session_id}",
                json.dumps(session.__dict__),
                ex=86400 * 7  # 7 days
            )
        
        logger.info(f"Session saved: {session_id} for {domain}")
        return session_id
    
    async def load_session(
        self,
        domain: str,
        user_id: Optional[str] = None,
        max_age_hours: int = 24,
    ) -> Optional[BrowserSession]:
        """
        Load a saved session.
        
        Args:
            domain: Website domain
            user_id: Optional user identifier
            max_age_hours: Maximum session age
            
        Returns:
            BrowserSession or None
        """
        session_id = self._get_session_id(domain, user_id)
        
        # Check memory cache
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if not session.is_expired(max_age_hours):
                session.last_used_at = time.time()
                return session
        
        # Check Redis
        await self._init_redis()
        if self._redis:
            data = await self._redis.get(f"session:{session_id}")
            if data:
                session_dict = json.loads(data)
                session = BrowserSession(**session_dict)
                if not session.is_expired(max_age_hours):
                    session.last_used_at = time.time()
                    self._sessions[session_id] = session
                    return session
        
        # Check local file
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                session_dict = json.load(f)
            session = BrowserSession(**session_dict)
            if not session.is_expired(max_age_hours):
                session.last_used_at = time.time()
                self._sessions[session_id] = session
                return session
        
        return None
    
    async def apply_to_playwright(
        self,
        context,
        domain: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Apply saved session to Playwright context."""
        session = await self.load_session(domain, user_id)
        if not session:
            return False
        
        # Add cookies
        if session.cookies:
            await context.add_cookies(session.cookies)
        
        logger.info(f"Session applied to Playwright: {session.id}")
        return True
    
    async def apply_to_selenium(
        self,
        driver,
        domain: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Apply saved session to Selenium driver."""
        session = await self.load_session(domain, user_id)
        if not session:
            return False
        
        # Navigate to domain first
        driver.get(f"https://{domain}")
        
        # Add cookies
        for cookie in session.cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Failed to add cookie: {e}")
        
        # Apply localStorage
        for key, value in session.local_storage.items():
            driver.execute_script(
                f"localStorage.setItem('{key}', '{value}')"
            )
        
        logger.info(f"Session applied to Selenium: {session.id}")
        return True
    
    async def save_from_playwright(
        self,
        context,
        domain: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Save session from Playwright context."""
        cookies = await context.cookies()
        
        # Get localStorage from page
        pages = context.pages
        local_storage = {}
        if pages:
            page = pages[0]
            try:
                local_storage = await page.evaluate("""
                    () => {
                        const items = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            items[key] = localStorage.getItem(key);
                        }
                        return items;
                    }
                """)
            except Exception:
                pass
        
        return await self.save_session(
            domain=domain,
            cookies=cookies,
            local_storage=local_storage,
            user_id=user_id,
        )
    
    async def save_from_selenium(
        self,
        driver,
        domain: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Save session from Selenium driver."""
        cookies = driver.get_cookies()
        
        # Get localStorage
        try:
            local_storage = driver.execute_script("""
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            """)
        except Exception:
            local_storage = {}
        
        return await self.save_session(
            domain=domain,
            cookies=cookies,
            local_storage=local_storage,
            user_id=user_id,
        )
    
    async def delete_session(
        self,
        domain: str,
        user_id: Optional[str] = None,
    ):
        """Delete a saved session."""
        session_id = self._get_session_id(domain, user_id)
        
        # Remove from memory
        self._sessions.pop(session_id, None)
        
        # Remove from file
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
        
        # Remove from Redis
        await self._init_redis()
        if self._redis:
            await self._redis.delete(f"session:{session_id}")
        
        logger.info(f"Session deleted: {session_id}")
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        sessions = []
        
        for session_file in self.storage_path.glob("*.json"):
            with open(session_file, 'r') as f:
                data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "domain": data["domain"],
                    "created_at": data["created_at"],
                    "last_used_at": data["last_used_at"],
                    "cookie_count": len(data["cookies"]),
                })
        
        return sessions


class SessionPool:
    """
    Pool of sessions for rate-limited scraping.
    
    Rotates through multiple authenticated sessions to avoid rate limits.
    """
    
    def __init__(
        self,
        manager: SessionManager,
        domain: str,
        max_sessions: int = 10,
        cooldown_seconds: int = 60,
    ):
        self.manager = manager
        self.domain = domain
        self.max_sessions = max_sessions
        self.cooldown_seconds = cooldown_seconds
        self._pool: List[str] = []  # Session IDs
        self._last_used: Dict[str, float] = {}
        self._lock = None
    
    async def _init_lock(self):
        """Initialize async lock."""
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
    
    async def add_session(self, user_id: str, cookies: List[Dict[str, Any]]):
        """Add a session to the pool."""
        session_id = await self.manager.save_session(
            domain=self.domain,
            cookies=cookies,
            user_id=user_id,
        )
        self._pool.append(session_id)
        self._last_used[session_id] = 0
        logger.info(f"Session added to pool: {session_id}")
    
    async def get_session(self) -> Optional[BrowserSession]:
        """Get an available session from the pool."""
        await self._init_lock()
        
        async with self._lock:
            now = time.time()
            
            # Find session with expired cooldown
            for session_id in self._pool:
                last_used = self._last_used.get(session_id, 0)
                if now - last_used > self.cooldown_seconds:
                    session = await self.manager.load_session(
                        self.domain,
                        user_id=session_id,
                    )
                    if session:
                        self._last_used[session_id] = now
                        return session
            
            return None
    
    async def release_session(self, session_id: str):
        """Release a session back to the pool."""
        # Session is automatically available after cooldown
        pass
    
    def pool_size(self) -> int:
        """Get current pool size."""
        return len(self._pool)


# Exports
__all__ = [
    "BrowserSession",
    "SessionManager",
    "SessionPool",
]
