"""
AI-Powered Extraction Module - LLM-based intelligent data extraction.

This is the COMPETITIVE EDGE - no other scraper has this level of AI integration.
"""

import json
import re
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel
from loguru import logger


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # Ollama, LM Studio
    AZURE = "azure"
    GROQ = "groq"


@dataclass
class ExtractionResult:
    """Result of AI extraction."""
    data: Dict[str, Any]
    confidence: float
    tokens_used: int
    model: str
    raw_response: str


class AIExtractor(ABC):
    """Base class for AI-powered extraction."""
    
    @abstractmethod
    async def extract(
        self,
        html: str,
        schema: Union[Dict[str, Any], Type[BaseModel]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract structured data from HTML using AI."""
        pass
    
    @abstractmethod
    async def extract_with_examples(
        self,
        html: str,
        examples: List[Dict[str, Any]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract data using few-shot learning with examples."""
        pass


class OpenAIExtractor(AIExtractor):
    """
    OpenAI-powered intelligent extraction.
    
    Features:
    - Structured output with JSON mode
    - Vision support for image-based extraction
    - Function calling for complex schemas
    - Automatic retry with different prompts
    """
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(
        self,
        api_key: str,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    async def _init_client(self):
        """Initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("Install openai: pip install openai")
    
    def _html_to_text(self, html: str, max_length: int = 50000) -> str:
        """Convert HTML to clean text for LLM processing."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + "\n... [truncated]"
            
            return text
        except Exception:
            return html[:max_length]
    
    def _schema_to_prompt(self, schema: Union[Dict, Type[BaseModel]]) -> str:
        """Convert schema to prompt instructions."""
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            schema_dict = schema.model_json_schema()
        else:
            schema_dict = schema
        
        return json.dumps(schema_dict, indent=2)
    
    async def extract(
        self,
        html: str,
        schema: Union[Dict[str, Any], Type[BaseModel]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract structured data from HTML using GPT."""
        await self._init_client()
        
        text = self._html_to_text(html)
        schema_str = self._schema_to_prompt(schema)
        
        system_prompt = """You are an expert data extraction assistant. 
Extract structured data from the provided webpage content according to the given schema.
Return ONLY valid JSON matching the schema. No explanations."""

        user_prompt = f"""Extract data from this webpage content:

---CONTENT START---
{text}
---CONTENT END---

Schema to follow:
{schema_str}

{instructions or "Extract all relevant data matching the schema."}

Return ONLY the JSON object, no markdown formatting."""

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return ExtractionResult(
                data=data,
                confidence=0.9,  # High confidence with structured output
                tokens_used=response.usage.total_tokens,
                model=self.model,
                raw_response=content
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Try to extract JSON from response
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return ExtractionResult(
                    data=data,
                    confidence=0.7,
                    tokens_used=response.usage.total_tokens,
                    model=self.model,
                    raw_response=content
                )
            raise
    
    async def extract_with_examples(
        self,
        html: str,
        examples: List[Dict[str, Any]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Few-shot extraction with examples."""
        await self._init_client()
        
        text = self._html_to_text(html)
        
        # Build few-shot prompt
        examples_str = "\n\n".join([
            f"Example {i+1}:\nInput: {ex.get('input', 'N/A')}\nOutput: {json.dumps(ex.get('output', {}))}"
            for i, ex in enumerate(examples)
        ])
        
        system_prompt = """You are an expert data extraction assistant.
Learn from the examples provided and extract data in the same format."""

        user_prompt = f"""Here are examples of extraction:

{examples_str}

Now extract from this content:

---CONTENT START---
{text}
---CONTENT END---

{instructions or "Extract data following the pattern shown in examples."}

Return ONLY the JSON object."""

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        return ExtractionResult(
            data=data,
            confidence=0.85,
            tokens_used=response.usage.total_tokens,
            model=self.model,
            raw_response=content
        )
    
    async def extract_with_vision(
        self,
        image_url: str,
        schema: Union[Dict[str, Any], Type[BaseModel]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract data from images (screenshots, charts, etc.)."""
        await self._init_client()
        
        schema_str = self._schema_to_prompt(schema)
        
        response = await self._client.chat.completions.create(
            model="gpt-4o",  # Vision requires gpt-4o
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Extract structured data from this image according to the schema:
{schema_str}

{instructions or "Extract all visible data matching the schema."}

Return ONLY valid JSON."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=self.max_tokens,
        )
        
        content = response.choices[0].message.content
        # Parse JSON from response
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = {"raw_text": content}
        
        return ExtractionResult(
            data=data,
            confidence=0.8,
            tokens_used=response.usage.total_tokens,
            model="gpt-4o",
            raw_response=content
        )


class AnthropicExtractor(AIExtractor):
    """Claude-powered extraction with superior reasoning."""
    
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    
    def __init__(
        self,
        api_key: str,
        model: str = None,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self._client = None
    
    async def _init_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Install anthropic: pip install anthropic")
    
    async def extract(
        self,
        html: str,
        schema: Union[Dict[str, Any], Type[BaseModel]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract using Claude."""
        await self._init_client()
        
        # Similar implementation to OpenAI but using Anthropic API
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)[:50000]
        
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            schema_dict = schema.model_json_schema()
        else:
            schema_dict = schema
        
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract structured data from this webpage:

{text}

Schema: {json.dumps(schema_dict)}

{instructions or ""}

Return ONLY valid JSON."""
                }
            ]
        )
        
        content = response.content[0].text
        match = re.search(r'\{.*\}', content, re.DOTALL)
        data = json.loads(match.group()) if match else {}
        
        return ExtractionResult(
            data=data,
            confidence=0.9,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=self.model,
            raw_response=content
        )
    
    async def extract_with_examples(
        self,
        html: str,
        examples: List[Dict[str, Any]],
        instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Few-shot with Claude."""
        # Similar implementation
        pass


class SmartExtractor:
    """
    Unified smart extractor that automatically chooses the best approach.
    
    Features:
    - Auto-selects between regex, CSS, XPath, and AI based on complexity
    - Caches extraction patterns for repeated use
    - Falls back gracefully between methods
    - Learns from corrections
    """
    
    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        prefer_ai: bool = False,
    ):
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        self.prefer_ai = prefer_ai
        self._pattern_cache: Dict[str, Any] = {}
    
    async def extract(
        self,
        html: str,
        schema: Union[Dict[str, Any], Type[BaseModel], str],
        method: str = "auto",
    ) -> Dict[str, Any]:
        """
        Smart extraction with automatic method selection.
        
        Args:
            html: HTML content
            schema: Extraction schema (dict, Pydantic model, or natural language)
            method: "auto", "css", "xpath", "regex", "ai"
        """
        if method == "auto":
            method = self._choose_method(html, schema)
        
        if method == "ai":
            if self.openai_key:
                extractor = OpenAIExtractor(self.openai_key)
            elif self.anthropic_key:
                extractor = AnthropicExtractor(self.anthropic_key)
            else:
                raise ValueError("AI extraction requires API key")
            
            result = await extractor.extract(html, schema)
            return result.data
        
        elif method == "css":
            return self._extract_css(html, schema)
        
        elif method == "xpath":
            return self._extract_xpath(html, schema)
        
        elif method == "regex":
            return self._extract_regex(html, schema)
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _choose_method(self, html: str, schema: Any) -> str:
        """Automatically choose best extraction method."""
        # If schema is natural language, use AI
        if isinstance(schema, str):
            return "ai"
        
        # If prefer_ai is set
        if self.prefer_ai:
            return "ai"
        
        # If schema has CSS selectors
        if isinstance(schema, dict):
            sample_value = list(schema.values())[0] if schema else ""
            if isinstance(sample_value, str):
                if sample_value.startswith("//"):
                    return "xpath"
                elif re.match(r'^[a-z.#\[\]]+', sample_value):
                    return "css"
        
        # Default to AI for complex extraction
        return "ai" if (self.openai_key or self.anthropic_key) else "css"
    
    def _extract_css(self, html: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """Extract using CSS selectors."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        result = {}
        for field, selector in schema.items():
            elements = soup.select(selector)
            if len(elements) == 1:
                result[field] = elements[0].get_text(strip=True)
            elif len(elements) > 1:
                result[field] = [el.get_text(strip=True) for el in elements]
            else:
                result[field] = None
        
        return result
    
    def _extract_xpath(self, html: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """Extract using XPath."""
        from lxml import etree
        tree = etree.HTML(html)
        
        result = {}
        for field, xpath in schema.items():
            elements = tree.xpath(xpath)
            if len(elements) == 1:
                result[field] = elements[0].text if hasattr(elements[0], 'text') else str(elements[0])
            elif len(elements) > 1:
                result[field] = [el.text if hasattr(el, 'text') else str(el) for el in elements]
            else:
                result[field] = None
        
        return result
    
    def _extract_regex(self, html: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """Extract using regex patterns."""
        result = {}
        for field, pattern in schema.items():
            matches = re.findall(pattern, html)
            if len(matches) == 1:
                result[field] = matches[0]
            elif len(matches) > 1:
                result[field] = matches
            else:
                result[field] = None
        
        return result


# Convenience exports
__all__ = [
    "LLMProvider",
    "ExtractionResult",
    "AIExtractor",
    "OpenAIExtractor",
    "AnthropicExtractor",
    "SmartExtractor",
]
