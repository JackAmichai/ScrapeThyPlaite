"""
Stealth and Anti-Detection Module - Browser fingerprint randomization and evasion.
"""

import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from scrape_thy_plaite.core.config import StealthConfig


@dataclass
class BrowserFingerprint:
    """Represents a browser fingerprint."""
    user_agent: str
    platform: str
    vendor: str
    renderer: str
    webgl_vendor: str
    screen_width: int
    screen_height: int
    color_depth: int
    timezone: str
    language: str
    languages: List[str]
    plugins: List[str]
    hardware_concurrency: int
    device_memory: int


class FingerprintGenerator:
    """
    Generate randomized browser fingerprints to evade detection.
    """
    
    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
        (1600, 900),
        (1680, 1050),
    ]
    
    # Common timezones
    TIMEZONES = [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    ]
    
    # Common languages
    LANGUAGES = [
        ["en-US", "en"],
        ["en-GB", "en"],
        ["de-DE", "de", "en"],
        ["fr-FR", "fr", "en"],
        ["es-ES", "es", "en"],
        ["ja-JP", "ja", "en"],
    ]
    
    # WebGL renderers
    WEBGL_RENDERERS = [
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (AMD)", "ANGLE (AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (Intel)", "ANGLE (Intel UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("Apple Inc.", "Apple M1"),
    ]
    
    # Hardware concurrency options
    HARDWARE_CONCURRENCY = [4, 6, 8, 12, 16]
    
    # Device memory options (GB)
    DEVICE_MEMORY = [4, 8, 16, 32]
    
    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or StealthConfig()
    
    def generate(self) -> BrowserFingerprint:
        """Generate a random browser fingerprint."""
        from scrape_thy_plaite.stealth.headers import get_random_user_agent, parse_user_agent
        
        user_agent = get_random_user_agent()
        ua_info = parse_user_agent(user_agent)
        
        resolution = random.choice(self.SCREEN_RESOLUTIONS)
        webgl = random.choice(self.WEBGL_RENDERERS)
        langs = random.choice(self.LANGUAGES)
        
        return BrowserFingerprint(
            user_agent=user_agent,
            platform=ua_info.get("platform", "Win32"),
            vendor="Google Inc.",
            renderer=webgl[1],
            webgl_vendor=webgl[0],
            screen_width=resolution[0],
            screen_height=resolution[1],
            color_depth=24,
            timezone=random.choice(self.TIMEZONES),
            language=langs[0],
            languages=langs,
            plugins=self._generate_plugins(),
            hardware_concurrency=random.choice(self.HARDWARE_CONCURRENCY),
            device_memory=random.choice(self.DEVICE_MEMORY),
        )
    
    def _generate_plugins(self) -> List[str]:
        """Generate a list of browser plugins."""
        plugins = [
            "Chrome PDF Plugin",
            "Chrome PDF Viewer",
            "Native Client",
        ]
        
        # Randomly add more plugins
        optional_plugins = [
            "Microsoft Edge PDF Plugin",
            "Adobe Acrobat",
            "Java Deployment Toolkit",
        ]
        
        for plugin in optional_plugins:
            if random.random() > 0.7:
                plugins.append(plugin)
        
        return plugins
    
    def to_stealth_scripts(self, fingerprint: BrowserFingerprint) -> List[str]:
        """Convert fingerprint to JavaScript injection scripts."""
        scripts = []
        
        # Navigator properties
        scripts.append(f"""
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint.platform}'
            }});
        """)
        
        scripts.append(f"""
            Object.defineProperty(navigator, 'vendor', {{
                get: () => '{fingerprint.vendor}'
            }});
        """)
        
        scripts.append(f"""
            Object.defineProperty(navigator, 'language', {{
                get: () => '{fingerprint.language}'
            }});
        """)
        
        scripts.append(f"""
            Object.defineProperty(navigator, 'languages', {{
                get: () => {fingerprint.languages}
            }});
        """)
        
        scripts.append(f"""
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint.hardware_concurrency}
            }});
        """)
        
        scripts.append(f"""
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint.device_memory}
            }});
        """)
        
        # Screen properties
        scripts.append(f"""
            Object.defineProperty(screen, 'width', {{
                get: () => {fingerprint.screen_width}
            }});
            Object.defineProperty(screen, 'height', {{
                get: () => {fingerprint.screen_height}
            }});
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {fingerprint.screen_width}
            }});
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {fingerprint.screen_height - 40}
            }});
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {fingerprint.color_depth}
            }});
        """)
        
        return scripts


def apply_stealth_scripts(config: StealthConfig) -> List[str]:
    """
    Generate stealth scripts based on configuration.
    
    Returns list of JavaScript code snippets to inject.
    """
    scripts = []
    
    # Hide webdriver
    if config.mask_webdriver:
        scripts.append("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Remove webdriver from prototype
            delete Object.getPrototypeOf(navigator).webdriver;
        """)
    
    # Mask automation indicators
    if config.mask_automation:
        scripts.append("""
            // Hide automation indicators
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    # Spoof plugins
    if config.spoof_plugins:
        scripts.append("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ];
                    plugins.length = 3;
                    return plugins;
                }
            });
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => {
                    const mimeTypes = [
                        { type: 'application/pdf', suffixes: 'pdf' },
                        { type: 'application/x-nacl', suffixes: '' }
                    ];
                    mimeTypes.length = 2;
                    return mimeTypes;
                }
            });
        """)
    
    # Spoof languages
    if config.spoof_languages:
        scripts.append("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
    
    # Spoof WebGL
    if config.spoof_webgl:
        scripts.append("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Google Inc. (NVIDIA)';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'ANGLE (NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)';
                }
                return getParameter.apply(this, arguments);
            };
        """)
    
    # Spoof audio context
    if config.spoof_audio_context:
        scripts.append("""
            const originalAudioContext = window.AudioContext || window.webkitAudioContext;
            if (originalAudioContext) {
                window.AudioContext = window.webkitAudioContext = function(...args) {
                    const context = new originalAudioContext(...args);
                    // Add small noise to audio fingerprint
                    const originalCreateAnalyser = context.createAnalyser.bind(context);
                    context.createAnalyser = function() {
                        const analyser = originalCreateAnalyser();
                        const originalGetFloatFrequencyData = analyser.getFloatFrequencyData.bind(analyser);
                        analyser.getFloatFrequencyData = function(array) {
                            originalGetFloatFrequencyData(array);
                            for (let i = 0; i < array.length; i++) {
                                array[i] += Math.random() * 0.0001;
                            }
                        };
                        return analyser;
                    };
                    return context;
                };
            }
        """)
    
    # Remove headless indicators
    scripts.append("""
        // Remove headless-specific properties
        const mockUserAgent = navigator.userAgent.replace('Headless', '');
        Object.defineProperty(navigator, 'userAgent', {
            get: () => mockUserAgent
        });
        
        // Fix window dimensions for headless
        if (window.outerWidth === 0) {
            Object.defineProperty(window, 'outerWidth', { get: () => screen.width });
        }
        if (window.outerHeight === 0) {
            Object.defineProperty(window, 'outerHeight', { get: () => screen.height });
        }
    """)
    
    # Add iframe contentWindow fix
    scripts.append("""
        // Fix iframe detection
        try {
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    return this._contentWindow || window;
                }
            });
        } catch (e) {}
    """)
    
    return scripts
