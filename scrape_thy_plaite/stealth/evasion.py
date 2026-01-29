"""
Evasion Module - Advanced anti-detection techniques.
"""

from typing import List
from scrape_thy_plaite.core.config import StealthConfig
from scrape_thy_plaite.stealth.fingerprint import apply_stealth_scripts as _apply_stealth_scripts


def apply_stealth_scripts(config: StealthConfig) -> List[str]:
    """Apply stealth scripts based on configuration."""
    return _apply_stealth_scripts(config)
