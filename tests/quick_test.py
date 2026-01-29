"""Quick test script to verify protection bypass capabilities."""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("🛡️  ScrapeThyPlaite - Protection Bypass Verification")
print("=" * 60)

print("\n📦 Testing imports...")

# Test antibot detection
from scrape_thy_plaite.stealth.antibot_detection import (
    ProtectionType, 
    ProtectionDetector, 
    detect_and_recommend,
    BypassStrategySelector
)
print("  ✓ Antibot detection module")

# Test CAPTCHA module
from scrape_thy_plaite.captcha import (
    CaptchaType,
    TwoCaptchaSolver,
    AntiCaptchaSolver,
)
print("  ✓ CAPTCHA module")

# Test protection type coverage
print("\n📋 Protection Types Supported:")
protection_types = [p.value for p in ProtectionType]
print(f"   Total: {len(protection_types)} protection systems")
for pt in protection_types:
    print(f"   ├─ {pt}")

# Test CAPTCHA types
print("\n🔑 CAPTCHA Types Supported:")
captcha_types = [ct.value for ct in CaptchaType]
print(f"   Total: {len(captcha_types)} CAPTCHA types")
for ct in captcha_types:
    print(f"   ├─ {ct}")

# Test detection for all major protections
print("\n🧪 Testing Protection Detection...")

tests = {
    "Cloudflare Bot Management": {
        "html": '<html><script src="/cdn-cgi/challenge-platform/scripts/challenge.js"></script></html>',
        "cookies": {"cf_clearance": "xxx"},
        "expected": "cloudflare"
    },
    "DataDome": {
        "html": '<html><script src="https://geo.captcha-delivery.com/captcha.js"></script></html>',
        "cookies": {"datadome": "xxx"},
        "expected": "datadome"
    },
    "Akamai Bot Manager": {
        "html": "",
        "cookies": {"_abck": "xxx", "bm_sz": "xxx"},
        "expected": "akamai"
    },
    "PerimeterX (Human Security)": {
        "html": '<html><script src="https://human-api.com/px.js"></script></html>',
        "cookies": {"_px": "xxx"},
        "expected": "perimeterx"
    },
    "Kasada": {
        "html": "",
        "cookies": {"x-kpsdk-ct": "xxx", "x-kpsdk-cd": "xxx"},
        "expected": "kasada"
    },
    "Arkose Labs (FunCaptcha)": {
        "html": '<html><script src="https://client-api.arkoselabs.com/fc/api"></script></html>',
        "cookies": {},
        "expected": "arkose"
    },
    "reCAPTCHA v2/v3": {
        "html": '<div class="g-recaptcha" data-sitekey="xxx"></div><script src="https://www.google.com/recaptcha/api.js"></script>',
        "cookies": {},
        "expected": "recaptcha"
    },
    "hCaptcha": {
        "html": '<div class="h-captcha" data-sitekey="xxx"></div><script src="https://hcaptcha.com/1/api.js"></script>',
        "cookies": {},
        "expected": "hcaptcha"
    },
    "Imperva/Incapsula": {
        "html": "",
        "cookies": {"incap_ses": "xxx", "visid_incap": "xxx"},
        "expected": "imperva"
    },
}

passed = 0
failed = 0

for name, test in tests.items():
    result = detect_and_recommend(
        test["html"], 
        {}, 
        test["cookies"], 
        403
    )
    detected = any(test["expected"] in p["type"] for p in result["protections"])
    
    if detected:
        print(f"   ✅ {name}: DETECTED")
        passed += 1
    else:
        print(f"   ❌ {name}: NOT DETECTED")
        failed += 1

print("\n" + "-" * 60)
print(f"📊 Detection Results: {passed}/{passed+failed} passed")

# Test strategy recommendations
print("\n🎯 Testing Bypass Strategy Recommendations...")

for protection_type in ProtectionType:
    strategies = BypassStrategySelector.STRATEGY_MAPPING.get(protection_type, [])
    if strategies:
        print(f"   {protection_type.value}: {', '.join(strategies)}")

# Verify CAPTCHA solving methods
print("\n🔐 Verifying CAPTCHA Solving Capabilities...")
required_methods = [
    "solve_recaptcha_v2",
    "solve_recaptcha_v3", 
    "solve_hcaptcha",
    "solve_turnstile",
    "solve_funcaptcha",
]

for solver_class in [TwoCaptchaSolver, AntiCaptchaSolver]:
    class_name = solver_class.__name__
    all_present = all(hasattr(solver_class, m) for m in required_methods)
    if all_present:
        print(f"   ✅ {class_name}: All methods present")
    else:
        missing = [m for m in required_methods if not hasattr(solver_class, m)]
        print(f"   ❌ {class_name}: Missing {missing}")

print("\n" + "=" * 60)
if failed == 0:
    print("🎉 ALL PROTECTION DETECTION TESTS PASSED!")
else:
    print(f"⚠️  {failed} test(s) failed - please review")
print("=" * 60)
