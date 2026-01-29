"""
CAPTCHA Solving Module - Integration with various CAPTCHA solving services.
Supports 2Captcha, Anti-Captcha, and CapMonster.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum

from loguru import logger

from scrape_thy_plaite.core.config import CaptchaConfig, CaptchaProvider
from scrape_thy_plaite.core.exceptions import (
    CaptchaError,
    CaptchaTimeoutError,
    CaptchaUnsolvableError,
    CaptchaProviderError,
    CaptchaInsufficientFundsError,
    ConfigurationError,
)


class CaptchaType(str, Enum):
    """Supported CAPTCHA types."""
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    RECAPTCHA_ENTERPRISE = "recaptcha_enterprise"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    TURNSTILE = "turnstile"
    IMAGE_CAPTCHA = "image"
    TEXT_CAPTCHA = "text"


class BaseCaptchaSolver(ABC):
    """Base class for CAPTCHA solvers."""
    
    def __init__(self, api_key: str, timeout: int = 120):
        self.api_key = api_key
        self.timeout = timeout
    
    @abstractmethod
    async def solve_recaptcha_v2(
        self, 
        site_key: str, 
        page_url: str,
        invisible: bool = False,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v2."""
        pass
    
    @abstractmethod
    async def solve_recaptcha_v3(
        self, 
        site_key: str, 
        page_url: str,
        action: str = "verify",
        min_score: float = 0.3,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v3."""
        pass
    
    @abstractmethod
    async def solve_hcaptcha(
        self, 
        site_key: str, 
        page_url: str,
        **kwargs
    ) -> str:
        """Solve hCaptcha."""
        pass
    
    @abstractmethod
    async def solve_turnstile(
        self,
        site_key: str,
        page_url: str,
        **kwargs
    ) -> str:
        """Solve Cloudflare Turnstile."""
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """Get account balance."""
        pass


class TwoCaptchaSolver(BaseCaptchaSolver):
    """
    2Captcha API integration.
    Website: https://2captcha.com
    """
    
    BASE_URL = "https://2captcha.com"
    
    def __init__(self, api_key: str, timeout: int = 120):
        super().__init__(api_key, timeout)
        self._client = None
    
    async def _init_client(self):
        """Initialize HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(timeout=30)
    
    async def _submit_task(self, params: Dict[str, Any]) -> str:
        """Submit a CAPTCHA task."""
        await self._init_client()
        
        params["key"] = self.api_key
        params["json"] = 1
        
        response = await self._client.post(
            f"{self.BASE_URL}/in.php",
            data=params
        )
        data = response.json()
        
        if data.get("status") != 1:
            error = data.get("request", "Unknown error")
            if "ERROR_ZERO_BALANCE" in error:
                raise CaptchaInsufficientFundsError(
                    "Insufficient balance", 
                    provider="2captcha",
                    error_code=error
                )
            raise CaptchaProviderError(
                f"Failed to submit CAPTCHA: {error}",
                provider="2captcha",
                error_code=error
            )
        
        return data["request"]  # Task ID
    
    async def _get_result(self, task_id: str) -> str:
        """Poll for CAPTCHA result."""
        await self._init_client()
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > self.timeout:
                raise CaptchaTimeoutError(
                    f"CAPTCHA solving timed out after {self.timeout}s"
                )
            
            await asyncio.sleep(5)  # Poll every 5 seconds
            
            response = await self._client.get(
                f"{self.BASE_URL}/res.php",
                params={
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                }
            )
            data = response.json()
            
            if data.get("status") == 1:
                return data["request"]
            
            if data.get("request") == "CAPCHA_NOT_READY":
                continue
            
            if "ERROR" in data.get("request", ""):
                raise CaptchaUnsolvableError(
                    f"CAPTCHA solving failed: {data['request']}"
                )
    
    async def solve_recaptcha_v2(
        self, 
        site_key: str, 
        page_url: str,
        invisible: bool = False,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v2."""
        logger.info(f"Solving reCAPTCHA v2 for {page_url}")
        
        params = {
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
        }
        
        if invisible:
            params["invisible"] = 1
        
        task_id = await self._submit_task(params)
        result = await self._get_result(task_id)
        
        logger.info("reCAPTCHA v2 solved successfully")
        return result
    
    async def solve_recaptcha_v3(
        self, 
        site_key: str, 
        page_url: str,
        action: str = "verify",
        min_score: float = 0.3,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v3."""
        logger.info(f"Solving reCAPTCHA v3 for {page_url}")
        
        params = {
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
            "version": "v3",
            "action": action,
            "min_score": min_score,
        }
        
        task_id = await self._submit_task(params)
        result = await self._get_result(task_id)
        
        logger.info("reCAPTCHA v3 solved successfully")
        return result
    
    async def solve_hcaptcha(
        self, 
        site_key: str, 
        page_url: str,
        **kwargs
    ) -> str:
        """Solve hCaptcha."""
        logger.info(f"Solving hCaptcha for {page_url}")
        
        params = {
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": page_url,
        }
        
        task_id = await self._submit_task(params)
        result = await self._get_result(task_id)
        
        logger.info("hCaptcha solved successfully")
        return result
    
    async def solve_turnstile(
        self,
        site_key: str,
        page_url: str,
        **kwargs
    ) -> str:
        """Solve Cloudflare Turnstile."""
        logger.info(f"Solving Turnstile for {page_url}")
        
        params = {
            "method": "turnstile",
            "sitekey": site_key,
            "pageurl": page_url,
        }
        
        task_id = await self._submit_task(params)
        result = await self._get_result(task_id)
        
        logger.info("Turnstile solved successfully")
        return result
    
    async def get_balance(self) -> float:
        """Get account balance."""
        await self._init_client()
        
        response = await self._client.get(
            f"{self.BASE_URL}/res.php",
            params={
                "key": self.api_key,
                "action": "getbalance",
                "json": 1,
            }
        )
        data = response.json()
        
        if data.get("status") == 1:
            return float(data["request"])
        
        raise CaptchaProviderError(
            f"Failed to get balance: {data.get('request')}",
            provider="2captcha"
        )


class AntiCaptchaSolver(BaseCaptchaSolver):
    """
    Anti-Captcha API integration.
    Website: https://anti-captcha.com
    """
    
    BASE_URL = "https://api.anti-captcha.com"
    
    def __init__(self, api_key: str, timeout: int = 120):
        super().__init__(api_key, timeout)
        self._client = None
    
    async def _init_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(timeout=30)
    
    async def _create_task(self, task: Dict[str, Any]) -> int:
        """Create a CAPTCHA task."""
        await self._init_client()
        
        response = await self._client.post(
            f"{self.BASE_URL}/createTask",
            json={
                "clientKey": self.api_key,
                "task": task,
            }
        )
        data = response.json()
        
        if data.get("errorId") != 0:
            raise CaptchaProviderError(
                f"Failed to create task: {data.get('errorDescription')}",
                provider="anticaptcha",
                error_code=data.get("errorCode")
            )
        
        return data["taskId"]
    
    async def _get_task_result(self, task_id: int) -> str:
        """Get task result."""
        await self._init_client()
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > self.timeout:
                raise CaptchaTimeoutError(
                    f"CAPTCHA solving timed out after {self.timeout}s"
                )
            
            await asyncio.sleep(5)
            
            response = await self._client.post(
                f"{self.BASE_URL}/getTaskResult",
                json={
                    "clientKey": self.api_key,
                    "taskId": task_id,
                }
            )
            data = response.json()
            
            if data.get("errorId") != 0:
                raise CaptchaProviderError(
                    f"Task failed: {data.get('errorDescription')}",
                    provider="anticaptcha",
                    error_code=data.get("errorCode")
                )
            
            if data.get("status") == "ready":
                return data["solution"]["gRecaptchaResponse"]
            
            # Still processing
    
    async def solve_recaptcha_v2(
        self, 
        site_key: str, 
        page_url: str,
        invisible: bool = False,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v2."""
        task = {
            "type": "RecaptchaV2TaskProxyless" if not invisible else "RecaptchaV2EnterpriseTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
        
        if invisible:
            task["isInvisible"] = True
        
        task_id = await self._create_task(task)
        return await self._get_task_result(task_id)
    
    async def solve_recaptcha_v3(
        self, 
        site_key: str, 
        page_url: str,
        action: str = "verify",
        min_score: float = 0.3,
        **kwargs
    ) -> str:
        """Solve reCAPTCHA v3."""
        task = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key,
            "pageAction": action,
            "minScore": min_score,
        }
        
        task_id = await self._create_task(task)
        return await self._get_task_result(task_id)
    
    async def solve_hcaptcha(
        self, 
        site_key: str, 
        page_url: str,
        **kwargs
    ) -> str:
        """Solve hCaptcha."""
        task = {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
        
        task_id = await self._create_task(task)
        result = await self._get_task_result(task_id)
        return result
    
    async def solve_turnstile(
        self,
        site_key: str,
        page_url: str,
        **kwargs
    ) -> str:
        """Solve Cloudflare Turnstile."""
        task = {
            "type": "TurnstileTaskProxyless",
            "websiteURL": page_url,
            "websiteKey": site_key,
        }
        
        task_id = await self._create_task(task)
        return await self._get_task_result(task_id)
    
    async def get_balance(self) -> float:
        """Get account balance."""
        await self._init_client()
        
        response = await self._client.post(
            f"{self.BASE_URL}/getBalance",
            json={"clientKey": self.api_key}
        )
        data = response.json()
        
        if data.get("errorId") == 0:
            return float(data["balance"])
        
        raise CaptchaProviderError(
            f"Failed to get balance: {data.get('errorDescription')}",
            provider="anticaptcha"
        )


class CaptchaSolver:
    """
    High-level CAPTCHA solver that wraps multiple providers.
    
    Example:
        solver = CaptchaSolver(config)
        token = await solver.solve(
            site_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            captcha_type="recaptcha_v2",
            page_url="https://example.com"
        )
    """
    
    def __init__(self, config: CaptchaConfig):
        self.config = config
        self._solver: Optional[BaseCaptchaSolver] = None
        
        if config.enabled and config.api_key:
            self._init_solver()
    
    def _init_solver(self) -> None:
        """Initialize the appropriate solver."""
        if self.config.provider == CaptchaProvider.TWO_CAPTCHA:
            self._solver = TwoCaptchaSolver(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        elif self.config.provider == CaptchaProvider.ANTICAPTCHA:
            self._solver = AntiCaptchaSolver(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        else:
            raise ConfigurationError(f"Unsupported provider: {self.config.provider}")
    
    async def solve(
        self,
        site_key: str,
        captcha_type: str,
        page_url: str,
        **kwargs
    ) -> str:
        """
        Solve a CAPTCHA.
        
        Args:
            site_key: The CAPTCHA site key
            captcha_type: Type of CAPTCHA (recaptcha_v2, recaptcha_v3, hcaptcha, turnstile)
            page_url: URL of the page with CAPTCHA
            **kwargs: Additional provider-specific arguments
            
        Returns:
            CAPTCHA solution token
        """
        if not self._solver:
            raise ConfigurationError("CAPTCHA solver not configured")
        
        captcha_type = CaptchaType(captcha_type)
        
        for attempt in range(self.config.max_retries):
            try:
                if captcha_type == CaptchaType.RECAPTCHA_V2:
                    return await self._solver.solve_recaptcha_v2(
                        site_key, page_url, **kwargs
                    )
                elif captcha_type == CaptchaType.RECAPTCHA_V3:
                    return await self._solver.solve_recaptcha_v3(
                        site_key, page_url, **kwargs
                    )
                elif captcha_type == CaptchaType.HCAPTCHA:
                    return await self._solver.solve_hcaptcha(
                        site_key, page_url, **kwargs
                    )
                elif captcha_type == CaptchaType.TURNSTILE:
                    return await self._solver.solve_turnstile(
                        site_key, page_url, **kwargs
                    )
                else:
                    raise CaptchaError(f"Unsupported CAPTCHA type: {captcha_type}")
                    
            except (CaptchaTimeoutError, CaptchaUnsolvableError) as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"CAPTCHA solve attempt {attempt + 1} failed, retrying...")
                    continue
                raise
        
        raise CaptchaError("All CAPTCHA solve attempts failed")
    
    async def get_balance(self) -> float:
        """Get solver account balance."""
        if not self._solver:
            raise ConfigurationError("CAPTCHA solver not configured")
        return await self._solver.get_balance()
