"""Optional LLM clients for enhanced metadata extraction."""

import json
import logging
from typing import Dict, List, Optional, Any

import requests

from .models import PaperMetadata

logger = logging.getLogger(__name__)


def _clean_json_response(text: str) -> str:
    """Strip markdown fences and whitespace from LLM JSON output."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    return text.strip()


def _build_prompt(title: str, authors: List[str], doi: str, abstract: str, content: str) -> str:
    return f"""Extract scholarly paper metadata from the following content.

Title: {title}
Authors: {', '.join(authors)}
DOI: {doi}
Abstract: {abstract}

Content (truncated): {content[:3000]}

Return ONLY a JSON object:
{{"title": "...", "authors": ["..."], "doi": "...", "arxiv_id": null, "publication_year": 2023, "journal": "...", "abstract": "...", "keywords": ["..."]}}"""


def _parse_llm_metadata(raw: str, fallback_title: str, fallback_authors: List[str], fallback_doi: str) -> Optional[PaperMetadata]:
    try:
        d = json.loads(_clean_json_response(raw))
        return PaperMetadata(
            title=d.get("title") or fallback_title,
            authors=d.get("authors") or fallback_authors,
            doi=d.get("doi") or fallback_doi,
            arxiv_id=d.get("arxiv_id"),
            publication_year=d.get("publication_year"),
            journal=d.get("journal"),
            abstract=d.get("abstract"),
            keywords=d.get("keywords", []),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        return None


class OllamaClient:
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("ollama_base_url", "http://localhost:11434")
        self.model = config.get("ollama_model", "llama2")
        self.timeout = config.get("ollama_timeout", 60)

    def extract_metadata(self, content: str, title: str, authors: List[str], doi: str, abstract: str) -> Optional[PaperMetadata]:
        prompt = _build_prompt(title, authors, doi, abstract, content)
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")
            return _parse_llm_metadata(raw, title, authors, doi)
        except Exception as e:
            logger.warning(f"Ollama extraction failed: {e}")
            return None


class OpenAIClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("openai_api_key")
        self.model = config.get("openai_model", "gpt-4")
        if not self.api_key:
            raise ValueError("openai_api_key is required for OpenAI client")

    def extract_metadata(self, content: str, title: str, authors: List[str], doi: str, abstract: str) -> Optional[PaperMetadata]:
        prompt = _build_prompt(title, authors, doi, abstract, content)
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            return _parse_llm_metadata(raw, title, authors, doi)
        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}")
            return None
