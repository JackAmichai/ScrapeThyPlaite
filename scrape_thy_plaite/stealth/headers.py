"""
HTTP Headers Management - User agent rotation and header generation.
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class UserAgentInfo:
    """Parsed user agent information."""
    browser: str
    version: str
    os: str
    platform: str


# Comprehensive list of real user agents (updated regularly)
CHROME_USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

FIREFOX_USER_AGENTS = [
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    
    # Mac Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Linux Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

EDGE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

SAFARI_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
]

MOBILE_USER_AGENTS = [
    # iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    
    # Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]

ALL_USER_AGENTS = (
    CHROME_USER_AGENTS + 
    FIREFOX_USER_AGENTS + 
    EDGE_USER_AGENTS + 
    SAFARI_USER_AGENTS
)


def get_random_user_agent(browser: Optional[str] = None, mobile: bool = False) -> str:
    """
    Get a random user agent string.
    
    Args:
        browser: Specific browser ('chrome', 'firefox', 'edge', 'safari')
        mobile: Whether to return a mobile user agent
        
    Returns:
        Random user agent string
    """
    if mobile:
        return random.choice(MOBILE_USER_AGENTS)
    
    if browser:
        browser = browser.lower()
        if browser == "chrome":
            return random.choice(CHROME_USER_AGENTS)
        elif browser == "firefox":
            return random.choice(FIREFOX_USER_AGENTS)
        elif browser == "edge":
            return random.choice(EDGE_USER_AGENTS)
        elif browser == "safari":
            return random.choice(SAFARI_USER_AGENTS)
    
    return random.choice(ALL_USER_AGENTS)


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Parse a user agent string to extract browser/OS info.
    
    Args:
        user_agent: User agent string to parse
        
    Returns:
        Dictionary with browser, version, os, platform
    """
    result = {
        "browser": "Unknown",
        "version": "Unknown",
        "os": "Unknown",
        "platform": "Win32",
    }
    
    # Detect browser
    if "Edg/" in user_agent:
        result["browser"] = "Edge"
        result["version"] = user_agent.split("Edg/")[1].split(" ")[0]
    elif "Chrome/" in user_agent:
        result["browser"] = "Chrome"
        result["version"] = user_agent.split("Chrome/")[1].split(" ")[0]
    elif "Firefox/" in user_agent:
        result["browser"] = "Firefox"
        result["version"] = user_agent.split("Firefox/")[1].split(" ")[0]
    elif "Safari/" in user_agent and "Chrome" not in user_agent:
        result["browser"] = "Safari"
        if "Version/" in user_agent:
            result["version"] = user_agent.split("Version/")[1].split(" ")[0]
    
    # Detect OS
    if "Windows NT 10" in user_agent:
        result["os"] = "Windows 10"
        result["platform"] = "Win32"
    elif "Windows NT 11" in user_agent:
        result["os"] = "Windows 11"
        result["platform"] = "Win32"
    elif "Macintosh" in user_agent:
        result["os"] = "macOS"
        result["platform"] = "MacIntel"
    elif "Linux" in user_agent:
        result["os"] = "Linux"
        result["platform"] = "Linux x86_64"
    elif "iPhone" in user_agent:
        result["os"] = "iOS"
        result["platform"] = "iPhone"
    elif "Android" in user_agent:
        result["os"] = "Android"
        result["platform"] = "Linux armv8l"
    
    return result


def generate_headers(
    user_agent: Optional[str] = None,
    referer: Optional[str] = None,
    accept_language: str = "en-US,en;q=0.9",
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Generate a complete set of HTTP headers.
    
    Args:
        user_agent: User agent string (random if not provided)
        referer: Referer header
        accept_language: Accept-Language header
        extra_headers: Additional headers to include
        
    Returns:
        Dictionary of headers
    """
    if not user_agent:
        user_agent = get_random_user_agent()
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
    }
    
    # Add Chrome-specific headers
    if "Chrome" in user_agent:
        headers["sec-ch-ua"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = '"Windows"'
    
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    
    if extra_headers:
        headers.update(extra_headers)
    
    return headers


class HeaderRotator:
    """
    Rotate headers for each request.
    """
    
    def __init__(
        self,
        rotate_user_agent: bool = True,
        user_agents: Optional[List[str]] = None
    ):
        self.rotate_user_agent = rotate_user_agent
        self.user_agents = user_agents or ALL_USER_AGENTS
        self._current_index = 0
    
    def get_headers(
        self, 
        referer: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get headers with rotated user agent."""
        user_agent = None
        
        if self.rotate_user_agent:
            user_agent = self.user_agents[self._current_index % len(self.user_agents)]
            self._current_index += 1
        
        return generate_headers(
            user_agent=user_agent,
            referer=referer,
            extra_headers=extra_headers
        )


# Accept headers for different content types
ACCEPT_HEADERS = {
    "html": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "json": "application/json, text/plain, */*",
    "image": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "script": "*/*",
    "style": "text/css,*/*;q=0.1",
    "font": "*/*",
    "all": "*/*",
}
