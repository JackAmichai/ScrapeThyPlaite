"""
Setup script for ScrapeThyPlaite.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="scrape-thy-plaite",
    version="1.0.0",
    author="ScrapeThyPlaite Team",
    author_email="contact@scrapethyplaite.dev",
    description="The most advanced open-source web scraping framework for AI companies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JackAmichai/ScrapeThyPlaite",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "httpx[http2]>=0.25.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.3",
        "pydantic>=2.5.0",
        "loguru>=0.7.2",
        "tenacity>=8.2.0",
        "fake-useragent>=1.4.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "selenium": [
            "selenium>=4.15.0",
            "webdriver-manager>=4.0.1",
        ],
        "undetected": [
            "undetected-chromedriver>=3.5.4",
        ],
        "playwright": [
            "playwright>=1.40.0",
        ],
        "cloudflare": [
            "cloudscraper>=1.2.71",
            "curl-cffi>=0.5.10",
        ],
        "captcha": [
            "2captcha-python>=1.2.1",
            "python-anticaptcha>=1.0.0",
        ],
        "all": [
            "selenium>=4.15.0",
            "webdriver-manager>=4.0.1",
            "undetected-chromedriver>=3.5.4",
            "playwright>=1.40.0",
            "cloudscraper>=1.2.71",
            "curl-cffi>=0.5.10",
            "2captcha-python>=1.2.1",
            "python-anticaptcha>=1.0.0",
            "pandas>=2.1.0",
            "pyarrow>=14.0.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scrape=scrape_thy_plaite.cli:main",
        ],
    },
    keywords=[
        "web scraping",
        "scraper",
        "crawler",
        "selenium",
        "playwright",
        "cloudflare bypass",
        "captcha solver",
        "anti-detection",
        "data extraction",
        "automation",
    ],
)
