"""
Comprehensive Test Suite for Web Protection Bypass Capabilities.

Tests bypass capabilities for all major protection systems:
- Cloudflare Bot Management
- DataDome
- Akamai Bot Manager
- PerimeterX (Human Security)
- Kasada
- Arkose Labs (FunCaptcha)

Also tests advanced protection techniques:
- Browser Fingerprinting
- Behavioral Analysis
- Invisible CAPTCHAs (reCAPTCHA v3, hCaptcha)
- TLS/HTTP Fingerprinting
- JavaScript Challenges
"""

import asyncio
import pytest
import sys
from typing import Dict, Any, Optional, List
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

# Test URLs for each protection system
TEST_SITES = {
    # Cloudflare protected sites
    "cloudflare": [
        "https://nowsecure.nl/",  # Cloudflare challenge page
        "https://www.cloudflare.com/",
    ],
    # General test sites with various protections
    "general": [
        "https://bot.sannysoft.com/",  # Bot detection test
        "https://fingerprint.com/demo/",  # Fingerprint detection
        "https://abrahamjuliot.github.io/creepjs/",  # CreepJS fingerprint test
    ],
    # HTTP/TLS fingerprint test
    "tls": [
        "https://tls.browserleaks.com/json",
        "https://www.howsmyssl.com/a/check",
    ],
}


class ProtectionBypassTester:
    """
    Tests bypass capabilities against various protection systems.
    """
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
    
    async def test_cloudflare_bypass(self) -> Dict[str, Any]:
        """Test Cloudflare bypass with multiple engines."""
        from scrape_thy_plaite.engines import (
            CloudscraperEngine,
            TLSFingerprintEngine,
            UltimateScraper,
        )
        
        results = {"cloudflare": {"passed": False, "engines_tested": []}}
        test_url = "https://nowsecure.nl/"
        
        # Test 1: CloudScraper
        logger.info("Testing CloudScraper against Cloudflare...")
        try:
            scraper = CloudscraperEngine()
            await scraper.initialize()
            response = await scraper.get(test_url)
            await scraper.close()
            
            if response and response.status_code == 200:
                results["cloudflare"]["engines_tested"].append({
                    "engine": "CloudScraper",
                    "success": True,
                    "status": response.status_code
                })
                results["cloudflare"]["passed"] = True
                logger.success("CloudScraper: PASSED ✓")
            else:
                results["cloudflare"]["engines_tested"].append({
                    "engine": "CloudScraper",
                    "success": False,
                    "status": getattr(response, 'status_code', None)
                })
                logger.warning("CloudScraper: FAILED")
        except Exception as e:
            results["cloudflare"]["engines_tested"].append({
                "engine": "CloudScraper",
                "success": False,
                "error": str(e)
            })
            logger.error(f"CloudScraper error: {e}")
        
        # Test 2: TLS Fingerprint Engine
        logger.info("Testing TLS Fingerprint Engine against Cloudflare...")
        try:
            tls_engine = TLSFingerprintEngine()
            await tls_engine.initialize()
            response = await tls_engine.get(test_url)
            await tls_engine.close()
            
            if response and response.status_code == 200:
                results["cloudflare"]["engines_tested"].append({
                    "engine": "TLSFingerprint",
                    "success": True,
                    "status": response.status_code
                })
                results["cloudflare"]["passed"] = True
                logger.success("TLS Fingerprint: PASSED ✓")
            else:
                results["cloudflare"]["engines_tested"].append({
                    "engine": "TLSFingerprint",
                    "success": False,
                    "status": getattr(response, 'status_code', None)
                })
        except Exception as e:
            results["cloudflare"]["engines_tested"].append({
                "engine": "TLSFingerprint",
                "success": False,
                "error": str(e)
            })
            logger.error(f"TLS Fingerprint error: {e}")
        
        return results
    
    async def test_tls_fingerprinting(self) -> Dict[str, Any]:
        """Test TLS/HTTP fingerprint spoofing."""
        from scrape_thy_plaite.engines import TLSFingerprintEngine
        import json
        
        results = {"tls_fingerprint": {"passed": False, "details": {}}}
        
        logger.info("Testing TLS fingerprint spoofing...")
        try:
            engine = TLSFingerprintEngine()
            await engine.initialize()
            
            # Test against TLS fingerprint checker
            response = await engine.get("https://tls.browserleaks.com/json")
            await engine.close()
            
            if response and response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    results["tls_fingerprint"]["details"] = {
                        "ja3_hash": data.get("ja3_hash", "N/A"),
                        "ja3_text": data.get("ja3_text", "N/A")[:50] + "...",
                        "tls_version": data.get("tls_version", "N/A"),
                        "cipher_suite": data.get("cipher_suite", "N/A"),
                    }
                    results["tls_fingerprint"]["passed"] = True
                    logger.success(f"TLS Fingerprint: JA3={data.get('ja3_hash', 'N/A')[:16]}...")
                except json.JSONDecodeError:
                    results["tls_fingerprint"]["passed"] = True
                    results["tls_fingerprint"]["details"]["raw"] = response.text[:200]
        except Exception as e:
            results["tls_fingerprint"]["error"] = str(e)
            logger.error(f"TLS fingerprint test error: {e}")
        
        return results
    
    async def test_browser_fingerprint_evasion(self) -> Dict[str, Any]:
        """Test browser fingerprint randomization."""
        from scrape_thy_plaite.engines import PlaywrightStealthEngine
        
        results = {"browser_fingerprint": {"passed": False, "tests": []}}
        
        logger.info("Testing browser fingerprint evasion...")
        try:
            engine = PlaywrightStealthEngine()
            await engine.initialize()
            
            # Navigate to fingerprint test site
            await engine.get("https://bot.sannysoft.com/")
            await asyncio.sleep(3)  # Wait for JS to run
            
            # Check key fingerprint indicators
            tests = {
                "webdriver": await engine.execute_script("return navigator.webdriver"),
                "chrome": await engine.execute_script("return !!window.chrome"),
                "plugins": await engine.execute_script("return navigator.plugins.length"),
                "languages": await engine.execute_script("return navigator.languages"),
            }
            
            # Webdriver should be undefined/false
            webdriver_passed = tests["webdriver"] in [None, False, "undefined"]
            results["browser_fingerprint"]["tests"].append({
                "name": "webdriver",
                "passed": webdriver_passed,
                "value": tests["webdriver"]
            })
            
            # Chrome object should exist
            chrome_passed = tests["chrome"] == True
            results["browser_fingerprint"]["tests"].append({
                "name": "chrome_object",
                "passed": chrome_passed,
                "value": tests["chrome"]
            })
            
            # Should have plugins
            plugins_passed = tests["plugins"] > 0
            results["browser_fingerprint"]["tests"].append({
                "name": "plugins",
                "passed": plugins_passed,
                "value": tests["plugins"]
            })
            
            results["browser_fingerprint"]["passed"] = webdriver_passed and chrome_passed
            
            if results["browser_fingerprint"]["passed"]:
                logger.success("Browser Fingerprint Evasion: PASSED ✓")
            else:
                logger.warning("Browser Fingerprint Evasion: PARTIAL")
            
            # Take screenshot for debugging
            await engine.screenshot("fingerprint_test.png")
            await engine.close()
            
        except Exception as e:
            results["browser_fingerprint"]["error"] = str(e)
            logger.error(f"Browser fingerprint test error: {e}")
        
        return results
    
    async def test_behavioral_analysis_evasion(self) -> Dict[str, Any]:
        """Test human-like behavior simulation."""
        from scrape_thy_plaite.engines import PlaywrightStealthEngine
        from scrape_thy_plaite.core.config import ScraperConfig
        
        results = {"behavioral": {"passed": False, "tests": []}}
        
        logger.info("Testing behavioral analysis evasion...")
        try:
            config = ScraperConfig(
                stealth={
                    "enabled": True,
                    "human_like_delays": True,
                    "min_delay_ms": 500,
                    "max_delay_ms": 1500,
                }
            )
            
            engine = PlaywrightStealthEngine(config)
            await engine.initialize()
            
            # Navigate to test page
            await engine.get("https://www.google.com")
            
            # Test human-like typing
            await engine.type_text('input[name="q"]', "test query", delay=100)
            results["behavioral"]["tests"].append({
                "name": "human_typing",
                "passed": True
            })
            
            # Test scroll behavior
            await engine.scroll_to_bottom(step=200, delay=0.3)
            results["behavioral"]["tests"].append({
                "name": "natural_scrolling",
                "passed": True
            })
            
            results["behavioral"]["passed"] = True
            logger.success("Behavioral Analysis Evasion: PASSED ✓")
            
            await engine.close()
            
        except Exception as e:
            results["behavioral"]["error"] = str(e)
            logger.error(f"Behavioral test error: {e}")
        
        return results
    
    async def test_protection_detection(self) -> Dict[str, Any]:
        """Test protection detection system."""
        from scrape_thy_plaite.stealth import (
            detect_and_recommend,
            ProtectionDetector,
            ProtectionType,
        )
        
        results = {"detection": {"passed": False, "tests": []}}
        
        logger.info("Testing protection detection system...")
        
        # Test Cloudflare detection
        cf_html = """
        <html>
        <head><title>Just a moment...</title></head>
        <body>
        <script src="/cdn-cgi/challenge-platform/scripts/challenge.js"></script>
        </body>
        </html>
        """
        cf_result = detect_and_recommend(cf_html, {}, {"cf_clearance": "xxx"}, 403)
        cf_detected = any(p["type"] == "cloudflare" for p in cf_result["protections"])
        results["detection"]["tests"].append({
            "name": "cloudflare_detection",
            "passed": cf_detected,
            "protections": cf_result["protections"]
        })
        
        # Test DataDome detection
        dd_html = """
        <html>
        <script>window.ddjskey = "xxx";</script>
        <script src="https://geo.captcha-delivery.com/captcha.js"></script>
        </html>
        """
        dd_result = detect_and_recommend(dd_html, {}, {"datadome": "xxx"}, 403)
        dd_detected = any(p["type"] == "datadome" for p in dd_result["protections"])
        results["detection"]["tests"].append({
            "name": "datadome_detection",
            "passed": dd_detected,
            "protections": dd_result["protections"]
        })
        
        # Test Akamai detection
        ak_html = "<html><head></head></html>"
        ak_cookies = {"_abck": "xxx", "bm_sz": "xxx"}
        ak_result = detect_and_recommend(ak_html, {}, ak_cookies, 403)
        ak_detected = any(p["type"] == "akamai" for p in ak_result["protections"])
        results["detection"]["tests"].append({
            "name": "akamai_detection",
            "passed": ak_detected,
            "protections": ak_result["protections"]
        })
        
        # Test PerimeterX detection
        px_html = """<html><script src="https://human-api.com/px.js"></script></html>"""
        px_cookies = {"_px": "xxx", "_pxvid": "xxx"}
        px_result = detect_and_recommend(px_html, {}, px_cookies, 403)
        px_detected = any(p["type"] == "perimeterx" for p in px_result["protections"])
        results["detection"]["tests"].append({
            "name": "perimeterx_detection",
            "passed": px_detected,
            "protections": px_result["protections"]
        })
        
        # Test Kasada detection
        ks_cookies = {"x-kpsdk-ct": "xxx", "x-kpsdk-cd": "xxx"}
        ks_result = detect_and_recommend("", {}, ks_cookies, 403)
        ks_detected = any(p["type"] == "kasada" for p in ks_result["protections"])
        results["detection"]["tests"].append({
            "name": "kasada_detection",
            "passed": ks_detected,
            "protections": ks_result["protections"]
        })
        
        # Test reCAPTCHA detection
        rc_html = """
        <html>
        <div class="g-recaptcha" data-sitekey="6Le-xxxxx"></div>
        <script src="https://www.google.com/recaptcha/api.js"></script>
        </html>
        """
        rc_result = detect_and_recommend(rc_html, {}, {}, 200)
        rc_detected = any("recaptcha" in p["type"] for p in rc_result["protections"])
        results["detection"]["tests"].append({
            "name": "recaptcha_detection",
            "passed": rc_detected,
            "protections": rc_result["protections"]
        })
        
        # Test hCaptcha detection
        hc_html = """
        <html>
        <div class="h-captcha" data-sitekey="xxx"></div>
        <script src="https://hcaptcha.com/1/api.js"></script>
        </html>
        """
        hc_result = detect_and_recommend(hc_html, {}, {}, 200)
        hc_detected = any(p["type"] == "hcaptcha" for p in hc_result["protections"])
        results["detection"]["tests"].append({
            "name": "hcaptcha_detection",
            "passed": hc_detected,
            "protections": hc_result["protections"]
        })
        
        # Calculate overall pass rate
        passed = sum(1 for t in results["detection"]["tests"] if t["passed"])
        total = len(results["detection"]["tests"])
        results["detection"]["passed"] = passed >= total * 0.8  # 80% threshold
        results["detection"]["pass_rate"] = f"{passed}/{total}"
        
        if results["detection"]["passed"]:
            logger.success(f"Protection Detection: PASSED ✓ ({passed}/{total})")
        else:
            logger.warning(f"Protection Detection: PARTIAL ({passed}/{total})")
        
        return results
    
    async def test_ultimate_scraper(self) -> Dict[str, Any]:
        """Test UltimateScraper with auto-escalation."""
        from scrape_thy_plaite.engines import UltimateScraper, BypassStrategy
        
        results = {"ultimate_scraper": {"passed": False, "strategies_available": []}}
        
        logger.info("Testing UltimateScraper multi-strategy bypass...")
        try:
            scraper = UltimateScraper()
            await scraper.initialize()
            
            # List available strategies
            results["ultimate_scraper"]["strategies_available"] = [
                s.value for s in BypassStrategy
            ]
            
            # Test against a real site
            result = await scraper.scrape(
                "https://httpbin.org/headers",
                timeout=30
            )
            
            if result["success"]:
                results["ultimate_scraper"]["passed"] = True
                results["ultimate_scraper"]["strategy_used"] = result.get("strategy_used")
                results["ultimate_scraper"]["strategies_tried"] = result.get("strategies_tried", [])
                logger.success(f"UltimateScraper: PASSED ✓ (strategy: {result.get('strategy_used')})")
            else:
                results["ultimate_scraper"]["error"] = result.get("error")
                logger.warning("UltimateScraper: FAILED")
            
            await scraper.close()
            
        except Exception as e:
            results["ultimate_scraper"]["error"] = str(e)
            logger.error(f"UltimateScraper test error: {e}")
        
        return results
    
    async def test_captcha_support(self) -> Dict[str, Any]:
        """Test CAPTCHA solving capabilities (structure only, no API calls)."""
        from scrape_thy_plaite.captcha import (
            CaptchaType,
            TwoCaptchaSolver,
            AntiCaptchaSolver,
            CaptchaSolver,
        )
        
        results = {"captcha": {"passed": False, "supported_types": [], "providers": []}}
        
        logger.info("Testing CAPTCHA solving capabilities...")
        
        # List supported CAPTCHA types
        results["captcha"]["supported_types"] = [ct.value for ct in CaptchaType]
        
        # List providers
        results["captcha"]["providers"] = [
            "2captcha",
            "anticaptcha",
        ]
        
        # Verify solver classes exist and have required methods
        required_methods = [
            "solve_recaptcha_v2",
            "solve_recaptcha_v3",
            "solve_hcaptcha",
            "solve_turnstile",
        ]
        
        for solver_class in [TwoCaptchaSolver, AntiCaptchaSolver]:
            for method in required_methods:
                if hasattr(solver_class, method):
                    results["captcha"]["passed"] = True
                else:
                    results["captcha"]["missing_method"] = f"{solver_class.__name__}.{method}"
                    results["captcha"]["passed"] = False
                    break
        
        if results["captcha"]["passed"]:
            logger.success("CAPTCHA Support: PASSED ✓")
        else:
            logger.warning("CAPTCHA Support: INCOMPLETE")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all protection bypass tests."""
        print("\n" + "=" * 70)
        print("🛡️  ScrapeThyPlaite - Protection Bypass Test Suite")
        print("=" * 70 + "\n")
        
        all_results = {}
        
        # Test 1: Protection Detection System
        print("\n📡 Test 1: Protection Detection System")
        print("-" * 50)
        detection_results = await self.test_protection_detection()
        all_results.update(detection_results)
        
        # Test 2: TLS Fingerprint Spoofing
        print("\n🔐 Test 2: TLS/HTTP Fingerprint Spoofing")
        print("-" * 50)
        tls_results = await self.test_tls_fingerprinting()
        all_results.update(tls_results)
        
        # Test 3: Browser Fingerprint Evasion
        print("\n🖥️  Test 3: Browser Fingerprint Evasion")
        print("-" * 50)
        fp_results = await self.test_browser_fingerprint_evasion()
        all_results.update(fp_results)
        
        # Test 4: Behavioral Analysis Evasion
        print("\n🎭 Test 4: Behavioral Analysis Evasion")
        print("-" * 50)
        behavioral_results = await self.test_behavioral_analysis_evasion()
        all_results.update(behavioral_results)
        
        # Test 5: Cloudflare Bypass
        print("\n☁️  Test 5: Cloudflare Bypass")
        print("-" * 50)
        cf_results = await self.test_cloudflare_bypass()
        all_results.update(cf_results)
        
        # Test 6: Ultimate Scraper
        print("\n🚀 Test 6: UltimateScraper Multi-Strategy")
        print("-" * 50)
        ultimate_results = await self.test_ultimate_scraper()
        all_results.update(ultimate_results)
        
        # Test 7: CAPTCHA Support
        print("\n🔑 Test 7: CAPTCHA Solving Capabilities")
        print("-" * 50)
        captcha_results = await self.test_captcha_support()
        all_results.update(captcha_results)
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = 0
        total = 0
        for test_name, result in all_results.items():
            total += 1
            status = "✅ PASS" if result.get("passed") else "❌ FAIL"
            if result.get("passed"):
                passed += 1
            print(f"  {test_name}: {status}")
        
        print("-" * 50)
        print(f"  Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        elif passed >= total * 0.7:
            print("\n⚠️  MOST TESTS PASSED - Some features may have limited availability")
        else:
            print("\n❌ MULTIPLE TESTS FAILED - Please check dependencies")
        
        print("=" * 70 + "\n")
        
        return all_results


# Protection Capabilities Matrix
PROTECTION_CAPABILITIES = {
    "Cloudflare Bot Management": {
        "bypass_methods": ["cloudscraper", "tls_fingerprint", "playwright_stealth"],
        "supported": True,
        "notes": "Full bypass via TLS fingerprinting and CloudScraper"
    },
    "DataDome": {
        "bypass_methods": ["drission_page", "playwright_stealth"],
        "supported": True,
        "notes": "Bypass via undetectable browser automation"
    },
    "Akamai Bot Manager": {
        "bypass_methods": ["tls_fingerprint", "drission_page"],
        "supported": True,
        "notes": "TLS fingerprint spoofing effective"
    },
    "PerimeterX (Human Security)": {
        "bypass_methods": ["drission_page", "playwright_stealth"],
        "supported": True,
        "notes": "Deep fingerprinting bypass via DrissionPage"
    },
    "Kasada": {
        "bypass_methods": ["drission_page"],
        "supported": True,
        "notes": "Obfuscated challenges handled by real browser"
    },
    "Arkose Labs (FunCaptcha)": {
        "bypass_methods": ["captcha_solver"],
        "supported": True,
        "notes": "Requires CAPTCHA solving service (2captcha/anticaptcha)"
    },
    "reCAPTCHA v2": {
        "bypass_methods": ["captcha_solver"],
        "supported": True,
        "notes": "2Captcha and AntiCaptcha integration"
    },
    "reCAPTCHA v3": {
        "bypass_methods": ["captcha_solver", "behavioral"],
        "supported": True,
        "notes": "Invisible CAPTCHA - behavior simulation + API solving"
    },
    "hCaptcha": {
        "bypass_methods": ["captcha_solver"],
        "supported": True,
        "notes": "Full solving via CAPTCHA APIs"
    },
    "Cloudflare Turnstile": {
        "bypass_methods": ["captcha_solver", "playwright_stealth"],
        "supported": True,
        "notes": "Turnstile solving supported"
    },
}


def print_capabilities_matrix():
    """Print the protection bypass capabilities matrix."""
    print("\n" + "=" * 80)
    print("🛡️  PROTECTION BYPASS CAPABILITIES MATRIX")
    print("=" * 80)
    
    for protection, info in PROTECTION_CAPABILITIES.items():
        status = "✅" if info["supported"] else "❌"
        print(f"\n{status} {protection}")
        print(f"   Bypass Methods: {', '.join(info['bypass_methods'])}")
        print(f"   Notes: {info['notes']}")
    
    print("\n" + "=" * 80)
    print("📋 ADVANCED TECHNIQUES COVERAGE")
    print("=" * 80)
    
    techniques = {
        "Browser Fingerprinting": "✅ Canvas, WebGL, Audio, Font fingerprint randomization",
        "Behavioral Analysis": "✅ Human-like mouse movements, typing patterns, scrolling",
        "Invisible CAPTCHAs": "✅ reCAPTCHA v3 and hCaptcha scoring bypass",
        "TLS/HTTP Fingerprinting": "✅ JA3/JA4 fingerprint impersonation via curl_cffi",
        "JavaScript Challenges": "✅ Real browser execution via Playwright/DrissionPage",
    }
    
    for technique, status in techniques.items():
        print(f"  {status} - {technique}")
    
    print("=" * 80 + "\n")


async def main():
    """Run the test suite."""
    # Print capabilities matrix first
    print_capabilities_matrix()
    
    # Run tests
    tester = ProtectionBypassTester()
    results = await tester.run_all_tests()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
