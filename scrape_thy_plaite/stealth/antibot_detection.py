"""
Anti-Bot Detection System - Comprehensive protection bypass.

This module implements detection and bypass strategies for various
anti-bot protection systems used by websites.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import re
from loguru import logger


class ProtectionType(Enum):
    """Types of anti-bot protection systems."""
    CLOUDFLARE = "cloudflare"
    CLOUDFLARE_TURNSTILE = "cloudflare_turnstile"
    DATADOME = "datadome"
    IMPERVA = "imperva"  # Incapsula
    AKAMAI = "akamai"
    PERIMETERX = "perimeterx"
    KASADA = "kasada"
    ARKOSE_LABS = "arkose_labs"  # FunCaptcha
    SHAPE_SECURITY = "shape_security"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


@dataclass
class ProtectionDetection:
    """Result of protection detection."""
    protection_type: ProtectionType
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]
    bypass_recommended: str  # Recommended bypass method


class ProtectionDetector:
    """
    Detects anti-bot protection systems from HTTP responses.
    """
    
    # Cloudflare detection patterns
    CLOUDFLARE_PATTERNS = [
        r'__cf_bm=',
        r'cf_clearance',
        r'cf-ray',
        r'cloudflare',
        r'cf-request-id',
        r'_cf_chl_tk',
        r'challenge-platform',
        r'cdn-cgi/challenge-platform',
        r'Attention Required! \| Cloudflare',
        r'Just a moment\.\.\.',
        r'Please Wait\.\.\. \| Cloudflare',
    ]
    
    # DataDome detection patterns
    DATADOME_PATTERNS = [
        r'datadome',
        r'dd_s',
        r'ddsid',
        r'ddid',
        r'datadome\.co/captcha',
        r'geo\.captcha-delivery\.com',
        r'DataDome',
        r'window\.ddjskey',
    ]
    
    # Imperva/Incapsula patterns
    IMPERVA_PATTERNS = [
        r'incap_ses',
        r'visid_incap',
        r'incapsula',
        r'reese84',
        r'___utmvc',
        r'imperva',
        r'Incapsula incident',
    ]
    
    # Akamai patterns
    AKAMAI_PATTERNS = [
        r'_abck',
        r'bm_sz',
        r'ak_bmsc',
        r'akamai',
        r'sensor_data',
        r'akam/',
        r'akamaihd\.net',
    ]
    
    # PerimeterX patterns
    PERIMETERX_PATTERNS = [
        r'_px\d?',
        r'_pxvid',
        r'_pxhd',
        r'pxcel',
        r'perimeterx',
        r'px-captcha',
        r'human-api\.com',
    ]
    
    # Kasada patterns
    KASADA_PATTERNS = [
        r'cd_s',
        r'x-kpsdk-cd',
        r'x-kpsdk-ct',
        r'x-kpsdk-im',
        r'kasada',
        r'/149e9513-01fa-4fb0-aad4-566afd725d1b/',
    ]
    
    # Arkose Labs (FunCaptcha) patterns
    ARKOSE_PATTERNS = [
        r'arkoselabs',
        r'funcaptcha',
        r'fc-token',
        r'arkose\.com',
        r'client-api\.arkoselabs\.com',
        r'arkoselabs\.io',
        r'FunCaptcha',
        r'enforcement\.arkoselabs\.com',
    ]
    
    # reCAPTCHA patterns
    RECAPTCHA_PATTERNS = [
        r'g-recaptcha',
        r'grecaptcha',
        r'recaptcha/api',
        r'www\.google\.com/recaptcha',
        r'data-sitekey',
        r'recaptcha-token',
    ]
    
    # hCaptcha patterns
    HCAPTCHA_PATTERNS = [
        r'h-captcha',
        r'hcaptcha',
        r'hcaptcha\.com',
        r'data-hcaptcha-widget',
    ]
    
    @classmethod
    def detect(
        cls,
        html: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        status_code: int = 200,
    ) -> List[ProtectionDetection]:
        """
        Detect protection systems from response.
        
        Args:
            html: Response HTML content
            headers: Response headers
            cookies: Response cookies
            status_code: HTTP status code
            
        Returns:
            List of detected protections
        """
        headers = headers or {}
        cookies = cookies or {}
        detections = []
        
        # Check Cloudflare
        cf_score = cls._check_patterns(
            cls.CLOUDFLARE_PATTERNS,
            html,
            headers,
            cookies
        )
        if cf_score > 0:
            # Check for Turnstile specifically
            is_turnstile = 'challenges.cloudflare.com' in html or 'turnstile' in html.lower()
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.CLOUDFLARE_TURNSTILE if is_turnstile else ProtectionType.CLOUDFLARE,
                confidence=min(cf_score * 0.3, 1.0),
                details={
                    "is_challenge_page": status_code == 403 or "Just a moment" in html,
                    "is_turnstile": is_turnstile,
                },
                bypass_recommended="cloudscraper" if not is_turnstile else "playwright_stealth"
            ))
        
        # Check DataDome
        dd_score = cls._check_patterns(
            cls.DATADOME_PATTERNS,
            html,
            headers,
            cookies
        )
        if dd_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.DATADOME,
                confidence=min(dd_score * 0.3, 1.0),
                details={
                    "has_captcha": "captcha-delivery.com" in html,
                },
                bypass_recommended="drission_page"
            ))
        
        # Check Imperva/Incapsula
        imp_score = cls._check_patterns(
            cls.IMPERVA_PATTERNS,
            html,
            headers,
            cookies
        )
        if imp_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.IMPERVA,
                confidence=min(imp_score * 0.3, 1.0),
                details={},
                bypass_recommended="tls_fingerprint"
            ))
        
        # Check Akamai
        ak_score = cls._check_patterns(
            cls.AKAMAI_PATTERNS,
            html,
            headers,
            cookies
        )
        if ak_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.AKAMAI,
                confidence=min(ak_score * 0.3, 1.0),
                details={},
                bypass_recommended="tls_fingerprint"
            ))
        
        # Check PerimeterX
        px_score = cls._check_patterns(
            cls.PERIMETERX_PATTERNS,
            html,
            headers,
            cookies
        )
        if px_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.PERIMETERX,
                confidence=min(px_score * 0.3, 1.0),
                details={},
                bypass_recommended="drission_page"
            ))
        
        # Check Kasada
        ks_score = cls._check_patterns(
            cls.KASADA_PATTERNS,
            html,
            headers,
            cookies
        )
        if ks_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.KASADA,
                confidence=min(ks_score * 0.3, 1.0),
                details={},
                bypass_recommended="drission_page"
            ))
        
        # Check Arkose Labs (FunCaptcha)
        arkose_score = cls._check_patterns(
            cls.ARKOSE_PATTERNS,
            html,
            headers,
            cookies
        )
        if arkose_score > 0:
            # Extract public key if possible
            public_key = cls._extract_arkose_key(html)
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.ARKOSE_LABS,
                confidence=min(arkose_score * 0.3, 1.0),
                details={
                    "public_key": public_key,
                },
                bypass_recommended="captcha_solver"
            ))
        
        # Check reCAPTCHA
        rc_score = cls._check_patterns(
            cls.RECAPTCHA_PATTERNS,
            html,
            headers,
            cookies
        )
        if rc_score > 0:
            # Determine v2 vs v3
            is_v3 = 'recaptcha/api.js?render=' in html
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.RECAPTCHA_V3 if is_v3 else ProtectionType.RECAPTCHA_V2,
                confidence=min(rc_score * 0.3, 1.0),
                details={
                    "version": "v3" if is_v3 else "v2",
                    "sitekey": cls._extract_sitekey(html, "recaptcha"),
                },
                bypass_recommended="captcha_solver"
            ))
        
        # Check hCaptcha
        hc_score = cls._check_patterns(
            cls.HCAPTCHA_PATTERNS,
            html,
            headers,
            cookies
        )
        if hc_score > 0:
            detections.append(ProtectionDetection(
                protection_type=ProtectionType.HCAPTCHA,
                confidence=min(hc_score * 0.3, 1.0),
                details={
                    "sitekey": cls._extract_sitekey(html, "hcaptcha"),
                },
                bypass_recommended="captcha_solver"
            ))
        
        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        return detections
    
    @classmethod
    def _check_patterns(
        cls,
        patterns: List[str],
        html: str,
        headers: Dict[str, str],
        cookies: Dict[str, str],
    ) -> int:
        """Count pattern matches."""
        score = 0
        search_text = html.lower()
        
        # Check HTML
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                score += 1
        
        # Check headers
        headers_str = str(headers).lower()
        for pattern in patterns:
            if re.search(pattern, headers_str, re.IGNORECASE):
                score += 1
        
        # Check cookies
        cookies_str = str(cookies).lower()
        for pattern in patterns:
            if re.search(pattern, cookies_str, re.IGNORECASE):
                score += 1
        
        return score
    
    @classmethod
    def _extract_sitekey(cls, html: str, captcha_type: str) -> Optional[str]:
        """Extract CAPTCHA sitekey from HTML."""
        if captcha_type == "recaptcha":
            # Try data-sitekey attribute
            match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
            if match:
                return match.group(1)
            
            # Try grecaptcha.render
            match = re.search(r'grecaptcha\.render\([^,]+,\s*\{[^}]*sitekey["\']?\s*:\s*["\']([^"\']+)["\']', html)
            if match:
                return match.group(1)
        
        elif captcha_type == "hcaptcha":
            match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def _extract_arkose_key(cls, html: str) -> Optional[str]:
        """Extract Arkose Labs (FunCaptcha) public key from HTML."""
        # Try data-public-key attribute
        match = re.search(r'data-public-key=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        
        # Try publicKey in JavaScript
        match = re.search(r'publicKey["\']?\s*[:=]\s*["\']([A-F0-9-]+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try pk parameter in URL
        match = re.search(r'[?&]pk=([A-F0-9-]+)', html, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None


class BypassStrategySelector:
    """
    Selects the best bypass strategy based on detected protections.
    """
    
    # Strategy priority for each protection type
    STRATEGY_MAPPING = {
        ProtectionType.CLOUDFLARE: ["cloudscraper", "tls_fingerprint", "undetected_chrome"],
        ProtectionType.CLOUDFLARE_TURNSTILE: ["playwright_stealth", "drission_page", "undetected_chrome"],
        ProtectionType.DATADOME: ["drission_page", "playwright_stealth", "tls_fingerprint"],
        ProtectionType.IMPERVA: ["tls_fingerprint", "cloudscraper", "drission_page"],
        ProtectionType.AKAMAI: ["tls_fingerprint", "drission_page", "playwright_stealth"],
        ProtectionType.PERIMETERX: ["drission_page", "playwright_stealth", "tls_fingerprint"],
        ProtectionType.KASADA: ["drission_page", "playwright_stealth"],
        ProtectionType.ARKOSE_LABS: ["captcha_solver", "drission_page"],
        ProtectionType.SHAPE_SECURITY: ["drission_page", "playwright_stealth"],
        ProtectionType.RECAPTCHA_V2: ["captcha_solver", "drission_page"],
        ProtectionType.RECAPTCHA_V3: ["captcha_solver", "playwright_stealth"],
        ProtectionType.HCAPTCHA: ["captcha_solver", "drission_page"],
        ProtectionType.FUNCAPTCHA: ["captcha_solver"],
        ProtectionType.CUSTOM: ["drission_page", "playwright_stealth", "undetected_chrome"],
        ProtectionType.UNKNOWN: ["cloudscraper", "tls_fingerprint", "playwright_stealth"],
    }
    
    @classmethod
    def select_strategies(
        cls,
        detections: List[ProtectionDetection],
        available_strategies: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Select optimal bypass strategies based on detections.
        
        Args:
            detections: List of detected protections
            available_strategies: List of available strategies (optional filter)
            
        Returns:
            Ordered list of recommended strategies
        """
        if not detections:
            return ["cloudscraper", "tls_fingerprint", "playwright_stealth"]
        
        # Get strategies for all detected protections
        all_strategies = []
        for detection in detections:
            strategies = cls.STRATEGY_MAPPING.get(
                detection.protection_type,
                ["drission_page", "playwright_stealth"]
            )
            # Weight by confidence
            for i, strategy in enumerate(strategies):
                weight = (len(strategies) - i) * detection.confidence
                all_strategies.append((strategy, weight))
        
        # Aggregate and sort by weight
        strategy_weights = {}
        for strategy, weight in all_strategies:
            strategy_weights[strategy] = strategy_weights.get(strategy, 0) + weight
        
        sorted_strategies = sorted(
            strategy_weights.keys(),
            key=lambda x: strategy_weights[x],
            reverse=True
        )
        
        # Filter by available strategies if specified
        if available_strategies:
            sorted_strategies = [
                s for s in sorted_strategies
                if s in available_strategies
            ]
        
        return sorted_strategies


def detect_and_recommend(
    html: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    status_code: int = 200,
) -> Dict[str, Any]:
    """
    Convenience function to detect protection and recommend bypass.
    
    Returns:
        Dict with 'protections', 'recommended_strategies', and 'details'
    """
    detections = ProtectionDetector.detect(html, headers, cookies, status_code)
    strategies = BypassStrategySelector.select_strategies(detections)
    
    return {
        "protections": [
            {
                "type": d.protection_type.value,
                "confidence": d.confidence,
                "details": d.details,
                "bypass": d.bypass_recommended,
            }
            for d in detections
        ],
        "recommended_strategies": strategies,
        "is_blocked": any(
            d.confidence > 0.5 and status_code in [403, 429, 503]
            for d in detections
        ),
    }


# Israeli site specific detection
class IsraeliSiteDetector:
    """
    Specialized detection for Israeli websites.
    """
    
    KNOWN_SITES = {
        "madlan.co.il": {
            "protections": ["datadome"],
            "strategies": ["drission_page", "playwright_stealth"],
            "notes": "Uses DataDome with aggressive fingerprinting",
        },
        "yad2.co.il": {
            "protections": ["custom"],
            "strategies": ["playwright_stealth", "tls_fingerprint"],
            "notes": "Custom protection with rate limiting",
        },
        "walla.co.il": {
            "protections": ["akamai"],
            "strategies": ["tls_fingerprint", "cloudscraper"],
            "notes": "Standard Akamai protection",
        },
        "calcalist.co.il": {
            "protections": ["cloudflare"],
            "strategies": ["cloudscraper"],
            "notes": "Basic Cloudflare",
        },
        "globes.co.il": {
            "protections": ["cloudflare"],
            "strategies": ["cloudscraper"],
            "notes": "Basic Cloudflare",
        },
    }
    
    @classmethod
    def get_site_info(cls, url: str) -> Optional[Dict[str, Any]]:
        """Get known information about an Israeli site."""
        for domain, info in cls.KNOWN_SITES.items():
            if domain in url:
                return {
                    "domain": domain,
                    **info
                }
        return None
    
    @classmethod
    def recommend_for_url(cls, url: str) -> List[str]:
        """Recommend strategies for a specific URL."""
        info = cls.get_site_info(url)
        if info:
            logger.info(f"Using known configuration for {info['domain']}: {info['notes']}")
            return info["strategies"]
        
        # Default for unknown Israeli sites
        return ["drission_page", "playwright_stealth", "tls_fingerprint"]
