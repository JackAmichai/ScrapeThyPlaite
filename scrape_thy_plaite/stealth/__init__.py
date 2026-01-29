"""Stealth module for anti-detection capabilities."""

from scrape_thy_plaite.stealth.fingerprint import FingerprintGenerator, BrowserFingerprint, apply_stealth_scripts
from scrape_thy_plaite.stealth.headers import (
    get_random_user_agent,
    parse_user_agent,
    generate_headers,
    HeaderRotator,
)
from scrape_thy_plaite.stealth.evasion import apply_stealth_scripts

__all__ = [
    "FingerprintGenerator",
    "BrowserFingerprint",
    "apply_stealth_scripts",
    "get_random_user_agent",
    "parse_user_agent",
    "generate_headers",
    "HeaderRotator",
]
