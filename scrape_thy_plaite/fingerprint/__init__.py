"""
Browser Fingerprint Rotation - Advanced anti-fingerprinting.

Competitive Edge: Dynamic fingerprint rotation to avoid detection.
"""

import random
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


# Browser profiles with realistic data
BROWSER_PROFILES = {
    "chrome_windows": {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "platform": "Win32",
        "vendor": "Google Inc.",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "languages": ["en-US", "en"],
        "timezone": "America/New_York",
        "screen": {"width": 1920, "height": 1080, "colorDepth": 24, "pixelRatio": 1},
        "hardwareConcurrency": 8,
        "deviceMemory": 8,
        "maxTouchPoints": 0,
    },
    "chrome_mac": {
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "platform": "MacIntel",
        "vendor": "Google Inc.",
        "webgl_vendor": "Google Inc. (Apple)",
        "webgl_renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
        "languages": ["en-US", "en"],
        "timezone": "America/Los_Angeles",
        "screen": {"width": 2560, "height": 1600, "colorDepth": 30, "pixelRatio": 2},
        "hardwareConcurrency": 10,
        "deviceMemory": 16,
        "maxTouchPoints": 0,
    },
    "firefox_windows": {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "platform": "Win32",
        "vendor": "",
        "webgl_vendor": "Mozilla",
        "webgl_renderer": "Mozilla (NVIDIA, NVIDIA GeForce RTX 3070 OpenGL Engine, OpenGL 4.6)",
        "languages": ["en-US", "en"],
        "timezone": "America/Chicago",
        "screen": {"width": 2560, "height": 1440, "colorDepth": 24, "pixelRatio": 1},
        "hardwareConcurrency": 12,
        "deviceMemory": 16,
        "maxTouchPoints": 0,
    },
    "safari_mac": {
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "platform": "MacIntel",
        "vendor": "Apple Computer, Inc.",
        "webgl_vendor": "Apple Inc.",
        "webgl_renderer": "Apple M2 Max",
        "languages": ["en-US"],
        "timezone": "America/Denver",
        "screen": {"width": 3456, "height": 2234, "colorDepth": 30, "pixelRatio": 2},
        "hardwareConcurrency": 12,
        "deviceMemory": 32,
        "maxTouchPoints": 0,
    },
    "edge_windows": {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "platform": "Win32",
        "vendor": "Google Inc.",
        "webgl_vendor": "Google Inc. (AMD)",
        "webgl_renderer": "ANGLE (AMD, AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "languages": ["en-US", "en"],
        "timezone": "America/Phoenix",
        "screen": {"width": 3840, "height": 2160, "colorDepth": 24, "pixelRatio": 1.5},
        "hardwareConcurrency": 16,
        "deviceMemory": 32,
        "maxTouchPoints": 0,
    },
}

# Additional WebGL renderers for variation
WEBGL_RENDERERS = [
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Apple, Apple M1, OpenGL 4.1)",
    "ANGLE (Apple, Apple M2, OpenGL 4.1)",
    "ANGLE (Apple, Apple M3 Pro, OpenGL 4.1)",
    "Mali-G78 MC14",
    "Adreno (TM) 660",
]

# Screen resolutions
SCREEN_RESOLUTIONS = [
    (1366, 768), (1440, 900), (1536, 864), (1600, 900),
    (1920, 1080), (2560, 1440), (3440, 1440), (3840, 2160),
    (2560, 1600), (2880, 1800), (3456, 2234),
]

# Timezones
TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Toronto", "Europe/London", "Europe/Paris", "Europe/Berlin",
    "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney",
]

# Font lists by platform
FONTS = {
    "windows": [
        "Arial", "Calibri", "Cambria", "Consolas", "Courier New",
        "Georgia", "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS",
        "Verdana", "Microsoft Sans Serif", "Palatino Linotype",
    ],
    "mac": [
        "Arial", "Avenir", "Georgia", "Helvetica", "Helvetica Neue",
        "Menlo", "Monaco", "San Francisco", "Times", "Trebuchet MS",
        "Verdana", "Futura", "Gill Sans",
    ],
    "linux": [
        "Arial", "Cantarell", "DejaVu Sans", "DejaVu Serif", "Droid Sans",
        "Liberation Mono", "Liberation Sans", "Noto Sans", "Ubuntu",
    ],
}


@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint."""
    user_agent: str
    platform: str
    vendor: str
    languages: List[str]
    timezone: str
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float
    hardware_concurrency: int
    device_memory: int
    max_touch_points: int
    webgl_vendor: str
    webgl_renderer: str
    fonts: List[str]
    plugins: List[str]
    canvas_hash: str
    audio_hash: str
    webrtc_enabled: bool
    do_not_track: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "userAgent": self.user_agent,
            "platform": self.platform,
            "vendor": self.vendor,
            "languages": self.languages,
            "timezone": self.timezone,
            "screen": {
                "width": self.screen_width,
                "height": self.screen_height,
                "colorDepth": self.color_depth,
                "pixelRatio": self.pixel_ratio,
            },
            "hardwareConcurrency": self.hardware_concurrency,
            "deviceMemory": self.device_memory,
            "maxTouchPoints": self.max_touch_points,
            "webgl": {
                "vendor": self.webgl_vendor,
                "renderer": self.webgl_renderer,
            },
            "fonts": self.fonts,
            "plugins": self.plugins,
            "canvasHash": self.canvas_hash,
            "audioHash": self.audio_hash,
            "webrtcEnabled": self.webrtc_enabled,
            "doNotTrack": self.do_not_track,
        }
    
    def get_fingerprint_hash(self) -> str:
        """Get unique hash of this fingerprint."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class FingerprintGenerator:
    """
    Generates realistic browser fingerprints.
    
    Features:
    - Consistent fingerprint generation (same seed = same fingerprint)
    - Cross-browser profile support
    - Realistic variation in properties
    - Avoids common detection patterns
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self._used_hashes: set = set()
    
    def generate(
        self,
        profile: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> BrowserFingerprint:
        """
        Generate a browser fingerprint.
        
        Args:
            profile: Browser profile (chrome_windows, firefox_windows, etc.)
            seed: Random seed for reproducibility
            
        Returns:
            Complete BrowserFingerprint
        """
        # Set random seed
        if seed is not None:
            random.seed(seed)
        elif self.seed is not None:
            random.seed(self.seed)
        
        # Select profile
        if profile is None:
            profile = random.choice(list(BROWSER_PROFILES.keys()))
        
        base = BROWSER_PROFILES.get(profile, BROWSER_PROFILES["chrome_windows"])
        
        # Determine platform
        platform = "windows" if "win" in base["platform"].lower() else "mac"
        if "linux" in base.get("userAgent", "").lower():
            platform = "linux"
        
        # Generate screen
        width, height = random.choice(SCREEN_RESOLUTIONS)
        pixel_ratio = random.choice([1, 1.25, 1.5, 2])
        
        # Generate hashes (unique per fingerprint)
        canvas_hash = hashlib.md5(
            f"canvas_{random.random()}".encode()
        ).hexdigest()[:32]
        audio_hash = hashlib.md5(
            f"audio_{random.random()}".encode()
        ).hexdigest()[:32]
        
        # Select fonts
        base_fonts = FONTS.get(platform, FONTS["windows"])
        font_count = random.randint(len(base_fonts) - 3, len(base_fonts))
        fonts = random.sample(base_fonts, font_count)
        
        # Generate plugins (varies by browser)
        plugins = self._generate_plugins(profile)
        
        fingerprint = BrowserFingerprint(
            user_agent=base["userAgent"],
            platform=base["platform"],
            vendor=base["vendor"],
            languages=base["languages"],
            timezone=random.choice(TIMEZONES),
            screen_width=width,
            screen_height=height,
            color_depth=random.choice([24, 30, 32]),
            pixel_ratio=pixel_ratio,
            hardware_concurrency=random.choice([4, 6, 8, 10, 12, 16]),
            device_memory=random.choice([4, 8, 16, 32]),
            max_touch_points=base["maxTouchPoints"],
            webgl_vendor=base["webgl_vendor"],
            webgl_renderer=random.choice(WEBGL_RENDERERS),
            fonts=fonts,
            plugins=plugins,
            canvas_hash=canvas_hash,
            audio_hash=audio_hash,
            webrtc_enabled=random.choice([True, False]),
            do_not_track=random.choice(["1", None]),
        )
        
        # Track used fingerprints to avoid duplicates
        fp_hash = fingerprint.get_fingerprint_hash()
        if fp_hash in self._used_hashes:
            # Regenerate with different seed
            return self.generate(profile, seed=random.randint(0, 1000000))
        
        self._used_hashes.add(fp_hash)
        return fingerprint
    
    def _generate_plugins(self, profile: str) -> List[str]:
        """Generate realistic plugin list."""
        if "chrome" in profile or "edge" in profile:
            return [
                "PDF Viewer",
                "Chrome PDF Viewer",
                "Chromium PDF Viewer",
                "Microsoft Edge PDF Viewer",
            ]
        elif "firefox" in profile:
            return []
        elif "safari" in profile:
            return ["WebKit PDF Plugin"]
        return []
    
    def generate_batch(
        self,
        count: int,
        profiles: Optional[List[str]] = None,
    ) -> List[BrowserFingerprint]:
        """
        Generate multiple unique fingerprints.
        
        Args:
            count: Number of fingerprints to generate
            profiles: List of profiles to use (cycles through)
            
        Returns:
            List of BrowserFingerprint objects
        """
        if profiles is None:
            profiles = list(BROWSER_PROFILES.keys())
        
        fingerprints = []
        for i in range(count):
            profile = profiles[i % len(profiles)]
            fingerprints.append(self.generate(profile))
        
        return fingerprints


class FingerprintInjector:
    """
    Injects fingerprints into browser instances.
    
    Supports Playwright and Selenium.
    """
    
    @staticmethod
    def get_playwright_context_options(
        fingerprint: BrowserFingerprint,
    ) -> Dict[str, Any]:
        """Get Playwright browser context options."""
        return {
            "user_agent": fingerprint.user_agent,
            "viewport": {
                "width": fingerprint.screen_width,
                "height": fingerprint.screen_height,
            },
            "device_scale_factor": fingerprint.pixel_ratio,
            "locale": fingerprint.languages[0].replace("-", "_"),
            "timezone_id": fingerprint.timezone,
            "color_scheme": "light",
            "reduced_motion": "no-preference",
        }
    
    @staticmethod
    def get_injection_script(fingerprint: BrowserFingerprint) -> str:
        """
        Get JavaScript to inject fingerprint overrides.
        
        This script overrides various browser properties.
        """
        fp = fingerprint.to_dict()
        
        return f"""
        // Override navigator properties
        Object.defineProperty(navigator, 'platform', {{ get: () => '{fp["platform"]}' }});
        Object.defineProperty(navigator, 'vendor', {{ get: () => '{fp["vendor"]}' }});
        Object.defineProperty(navigator, 'languages', {{ get: () => {json.dumps(fp["languages"])} }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {fp["hardwareConcurrency"]} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {fp["deviceMemory"]} }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => {fp["maxTouchPoints"]} }});
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{ get: () => {fp["screen"]["width"]} }});
        Object.defineProperty(screen, 'height', {{ get: () => {fp["screen"]["height"]} }});
        Object.defineProperty(screen, 'colorDepth', {{ get: () => {fp["screen"]["colorDepth"]} }});
        Object.defineProperty(screen, 'pixelDepth', {{ get: () => {fp["screen"]["colorDepth"]} }});
        Object.defineProperty(window, 'devicePixelRatio', {{ get: () => {fp["screen"]["pixelRatio"]} }});
        
        // Override WebGL
        const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fp["webgl"]["vendor"]}';
            if (parameter === 37446) return '{fp["webgl"]["renderer"]}';
            return getParameterOriginal.apply(this, arguments);
        }};
        
        const getParameter2Original = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fp["webgl"]["vendor"]}';
            if (parameter === 37446) return '{fp["webgl"]["renderer"]}';
            return getParameter2Original.apply(this, arguments);
        }};
        
        // Prevent canvas fingerprinting
        const toDataURLOriginal = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            if (type === 'image/png' || type === 'image/webp') {{
                // Add slight noise to canvas
                const ctx = this.getContext('2d');
                if (ctx) {{
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        imageData.data[i] ^= (Math.random() * 2 | 0);
                    }}
                    ctx.putImageData(imageData, 0, 0);
                }}
            }}
            return toDataURLOriginal.apply(this, arguments);
        }};
        
        // Override timezone
        const DateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(locale, options) {{
            return new DateTimeFormat(locale, {{ ...options, timeZone: '{fp["timezone"]}' }});
        }};
        
        console.log('[FingerprintInjector] Fingerprint applied');
        """
    
    @staticmethod
    async def inject_playwright(page, fingerprint: BrowserFingerprint):
        """Inject fingerprint into Playwright page."""
        script = FingerprintInjector.get_injection_script(fingerprint)
        await page.add_init_script(script)
    
    @staticmethod
    def inject_selenium(driver, fingerprint: BrowserFingerprint):
        """Inject fingerprint into Selenium driver."""
        script = FingerprintInjector.get_injection_script(fingerprint)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": script
        })


class FingerprintRotator:
    """
    Automatically rotates fingerprints during scraping.
    
    Features:
    - Rotate after N requests
    - Rotate on detection
    - Domain-specific fingerprints
    """
    
    def __init__(
        self,
        rotate_every: int = 50,
        profiles: Optional[List[str]] = None,
    ):
        self.rotate_every = rotate_every
        self.profiles = profiles or list(BROWSER_PROFILES.keys())
        self.generator = FingerprintGenerator()
        self._request_count = 0
        self._current_fingerprint: Optional[BrowserFingerprint] = None
        self._domain_fingerprints: Dict[str, BrowserFingerprint] = {}
    
    def get_fingerprint(self, domain: Optional[str] = None) -> BrowserFingerprint:
        """
        Get current fingerprint, rotating if needed.
        
        Args:
            domain: Optional domain for domain-specific fingerprints
            
        Returns:
            BrowserFingerprint to use
        """
        self._request_count += 1
        
        # Check for domain-specific fingerprint
        if domain and domain in self._domain_fingerprints:
            return self._domain_fingerprints[domain]
        
        # Check if rotation needed
        if (
            self._current_fingerprint is None or 
            self._request_count % self.rotate_every == 0
        ):
            self._current_fingerprint = self.generator.generate(
                random.choice(self.profiles)
            )
        
        return self._current_fingerprint
    
    def force_rotate(self) -> BrowserFingerprint:
        """Force fingerprint rotation."""
        self._current_fingerprint = self.generator.generate(
            random.choice(self.profiles)
        )
        return self._current_fingerprint
    
    def set_domain_fingerprint(
        self,
        domain: str,
        fingerprint: Optional[BrowserFingerprint] = None,
    ):
        """
        Set a specific fingerprint for a domain.
        
        Args:
            domain: Domain to set fingerprint for
            fingerprint: Fingerprint to use (generates one if None)
        """
        if fingerprint is None:
            fingerprint = self.generator.generate()
        self._domain_fingerprints[domain] = fingerprint
    
    def reset(self):
        """Reset rotator state."""
        self._request_count = 0
        self._current_fingerprint = None
        self._domain_fingerprints.clear()


# Exports
__all__ = [
    "BrowserFingerprint",
    "FingerprintGenerator",
    "FingerprintInjector",
    "FingerprintRotator",
    "BROWSER_PROFILES",
]
