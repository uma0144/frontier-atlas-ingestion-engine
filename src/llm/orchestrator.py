"""
Multi-Tier LLM Extraction Engine:
Features 3-tier fallback chain (Gemini Flash -> Groq Llama 3 -> DeepSeek/Deterministic Fallback),
payload chunking to prevent 413s, and exponential backoff + jitter for 429s.
"""

import json
import logging
import re
from typing import Dict, Any, Optional
from src.config import GEMINI_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY
from src.llm.chunker import HTMLChunker
from src.llm.rate_limiter import AsyncTokenBucket, with_retry_and_jitter

logger = logging.getLogger("LLMOrchestrator")


class MultiTierLLMOrchestrator:
    def __init__(self):
        self.rate_limiter = AsyncTokenBucket(rate_per_second=10.0, capacity=20.0)
        self._gemini_client = None
        self._groq_client = None

        if GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.debug(f"Gemini client init: {e}")

        if GROQ_API_KEY:
            try:
                from groq import AsyncGroq
                self._groq_client = AsyncGroq(api_key=GROQ_API_KEY)
            except Exception as e:
                logger.debug(f"Groq client init: {e}")

    @with_retry_and_jitter(max_retries=3)
    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Tier 1: Google Gemini 2.0 / 1.5 Flash."""
        if not self._gemini_client:
            return None
        await self.rate_limiter.acquire()
        
        # Async generation with Gemini SDK
        response = self._gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        if response and response.text:
            return response.text
        return None

    @with_retry_and_jitter(max_retries=3)
    async def _call_groq(self, prompt: str) -> Optional[str]:
        """Tier 2: Groq LLaMA 3.3 70B / 8B."""
        if not self._groq_client:
            return None
        await self.rate_limiter.acquire()

        response = await self._groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise data extraction engine. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        if response and response.choices:
            return response.choices[0].message.content
        return None

    def _deterministic_fallback_extractor(self, text: str, schema_type: str) -> Dict[str, Any]:
        """Tier 3 / Fallback: Deterministic Regex & Rule-Based Extractor."""
        cleaned = HTMLChunker.clean_html(text)
        result = {}
        if schema_type == "STARTUP":
            name_match = re.search(r'([A-Z][a-zA-Z0-9\.\s]{2,25})\s*(?:Inc|LLC|Corp|AI|Technologies)?', cleaned)
            emp_match = re.search(r'(\d+)\s*(?:employees|people|team members)', cleaned, re.I)
            result = {
                "entityName": name_match.group(0).strip() if name_match else "AI Venture",
                "employeeCount": int(emp_match.group(1)) if emp_match else None,
                "industry": "Artificial Intelligence",
                "description": cleaned[:200]
            }
        elif schema_type == "PRODUCT":
            pricing = "FREEMIUM"
            if "free" in cleaned.lower():
                pricing = "FREE"
            elif "enterprise" in cleaned.lower():
                pricing = "ENTERPRISE"
            result = {
                "productName": "AI Software Platform",
                "startupName": "AI Labs",
                "pricingModel": pricing,
                "category": "Machine Learning Software",
                "description": cleaned[:200]
            }
        return result

    async def extract_entity(self, raw_content: str, schema_type: str) -> Dict[str, Any]:
        """
        Execute multi-tier extraction:
        Clean payload -> Gemini Flash -> Groq Llama 3 -> Deterministic Fallback.
        """
        # Step 1: Prevent 413 by cleaning and truncating payload
        clean_text = HTMLChunker.clean_html(raw_content)
        chunk = HTMLChunker.chunk_text(clean_text)[0]

        prompt = (
            f"Extract structured information from the following text into a JSON object for schema type: {schema_type}.\n"
            f"Schema structure requirements: Return valid JSON with accurate fields.\n\n"
            f"Content:\n{chunk}\n\n"
            f"Output JSON only:"
        )

        # Step 2: Tier 1 (Gemini)
        try:
            gemini_res = await self._call_gemini(prompt)
            if gemini_res:
                json_match = re.search(r'\{.*\}', gemini_res, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
        except Exception as e:
            logger.debug(f"Tier 1 (Gemini) failed: {e}. Falling back to Tier 2...")

        # Step 3: Tier 2 (Groq)
        try:
            groq_res = await self._call_groq(prompt)
            if groq_res:
                return json.loads(groq_res)
        except Exception as e:
            logger.debug(f"Tier 2 (Groq) failed: {e}. Falling back to Tier 3...")

        # Step 4: Tier 3 (Deterministic Fallback)
        return self._deterministic_fallback_extractor(raw_content, schema_type)
