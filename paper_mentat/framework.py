"""Main framework: orchestrates search, OA verification, and PDF retrieval."""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml

from .apis import ScholarlyAPIClient
from .models import OAColor, PaperMetadata, ProcessingResult, ProcessingState

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "rate_limit_per_second": 1,
    "max_retries": 3,
    "timeout": 30,
    "user_agent": "AcademicPaperFramework/1.0 (research-agent)",
    "contact_email": "",
    "output_dir": "results",
    "save_pdfs": True,
    "topics_of_interest": [],
    "paper_lists": [],
    "enable_llm_enhancement": False,
    "llm_provider": "ollama",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama2",
    "ollama_timeout": 60,
}


class AcademicPaperFramework:
    def __init__(self, config_path: Optional[str] = None):
        self.config = dict(DEFAULT_CONFIG)
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                self.config.update(yaml.safe_load(f) or {})
        self.api = ScholarlyAPIClient(self.config)
        self.llm_client = None
        if self.config.get("enable_llm_enhancement"):
            self._setup_llm()

    def _setup_llm(self):
        provider = self.config.get("llm_provider", "ollama")
        try:
            if provider == "ollama":
                from .llm import OllamaClient
                self.llm_client = OllamaClient(self.config)
            elif provider == "openai":
                from .llm import OpenAIClient
                self.llm_client = OpenAIClient(self.config)
        except Exception as e:
            logger.warning(f"LLM setup failed: {e}")

    # ── Search methods ────────────────────────────────────────────────

    def search_ad_hoc(self, query: str, max_results: int = 50) -> List[ProcessingResult]:
        """Search across arXiv, Crossref, and OpenAlex for papers matching query."""
        logger.info(f"Ad-hoc search: {query}")
        results: List[ProcessingResult] = []
        seen_keys: set = set()
        per_source = max(max_results // 3, 5)

        # arXiv - returns full metadata directly
        for meta in self.api.arxiv_search(query, per_source):
            key = meta.arxiv_id or meta.title
            if key in seen_keys:
                continue
            seen_keys.add(key)
            results.append(ProcessingResult(
                url=f"https://arxiv.org/abs/{meta.arxiv_id}" if meta.arxiv_id else "",
                state=ProcessingState.COMPLETED,
                metadata=meta,
            ))

        # Crossref
        for item in self.api.crossref_search(query, per_source):
            meta = ScholarlyAPIClient.crossref_to_metadata(item)
            if meta.doi and meta.doi in seen_keys:
                continue
            if meta.doi:
                seen_keys.add(meta.doi)
            # Try OA check via Unpaywall
            meta = self._enrich_oa(meta)
            state = ProcessingState.COMPLETED if meta.oa_url else ProcessingState.METADATA_EXTRACTED
            results.append(ProcessingResult(
                url=f"https://doi.org/{meta.doi}" if meta.doi else "",
                state=state,
                metadata=meta,
            ))

        # OpenAlex
        for item in self.api.openalex_search(query, per_source):
            meta = ScholarlyAPIClient.openalex_to_metadata(item)
            key = meta.doi or meta.title
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if meta.doi and not meta.oa_url:
                meta = self._enrich_oa(meta)
            state = ProcessingState.COMPLETED if meta.oa_url else ProcessingState.METADATA_EXTRACTED
            results.append(ProcessingResult(
                url=f"https://doi.org/{meta.doi}" if meta.doi else "",
                state=state,
                metadata=meta,
            ))

        return results[:max_results]

    def search_by_topics(self, topics: List[str], max_results_per_topic: int = 20) -> List[ProcessingResult]:
        all_results: List[ProcessingResult] = []
        for topic in topics:
            logger.info(f"Topic search: {topic}")
            all_results.extend(self.search_ad_hoc(topic, max_results_per_topic))
        return all_results

    # ── Paper list processing ─────────────────────────────────────────

    def process_paper_list(self, file_path: str) -> List[ProcessingResult]:
        """Process a file of DOIs and URLs."""
        logger.info(f"Processing paper list: {file_path}")
        entries = self._parse_paper_list(file_path)
        results: List[ProcessingResult] = []
        for entry in entries:
            result = self._process_entry(entry)
            results.append(result)
        return results

    def _parse_paper_list(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        with open(file_path) as f:
            text = f.read()
        entries: List[str] = []
        # Extract DOIs
        for doi in re.findall(r"10\.\d{4,9}/[^\s]+", text):
            entries.append(doi.rstrip(".,;)"))
        # Extract URLs (that aren't already doi.org links)
        for url in re.findall(r"https?://[^\s<>\"]+", text):
            url = url.rstrip(".,;)")
            if "doi.org" not in url:
                entries.append(url)
        return list(dict.fromkeys(entries))  # dedupe preserving order

    def _process_entry(self, entry: str) -> ProcessingResult:
        start = time.time()
        try:
            if entry.startswith("http"):
                return self._process_url(entry, start)
            else:
                return self._process_doi(entry, start)
        except Exception as e:
            logger.error(f"Error processing {entry}: {e}")
            return ProcessingResult(
                url=entry, state=ProcessingState.FAILED,
                error_message=str(e), processing_time=time.time() - start,
            )

    def _process_doi(self, doi: str, start: float) -> ProcessingResult:
        # Look up via Crossref
        item = self.api.crossref_lookup_doi(doi)
        if not item:
            return ProcessingResult(
                url=f"https://doi.org/{doi}", state=ProcessingState.FAILED,
                error_message="DOI not found in Crossref", processing_time=time.time() - start,
            )
        meta = ScholarlyAPIClient.crossref_to_metadata(item)
        meta = self._enrich_oa(meta)
        state = ProcessingState.COMPLETED if meta.oa_url else ProcessingState.METADATA_EXTRACTED
        return ProcessingResult(
            url=f"https://doi.org/{doi}", state=state,
            metadata=meta, processing_time=time.time() - start,
        )

    def _process_url(self, url: str, start: float) -> ProcessingResult:
        # Handle arXiv URLs directly
        arxiv_match = re.search(r"arxiv\.org/abs/(\S+)", url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            pdf_url = url.replace("/abs/", "/pdf/")
            meta = PaperMetadata(
                title=f"arXiv:{arxiv_id}", arxiv_id=arxiv_id,
                oa_status=OAColor.GREEN, oa_url=pdf_url,
            )
            return ProcessingResult(
                url=url, state=ProcessingState.COMPLETED,
                metadata=meta, processing_time=time.time() - start,
            )
        # For other URLs, try to extract a DOI
        doi_match = re.search(r"10\.\d{4,9}/[^\s]+", url)
        if doi_match:
            return self._process_doi(doi_match.group().rstrip(".,;)"), start)
        # Generic URL - just record it
        return ProcessingResult(
            url=url, state=ProcessingState.METADATA_EXTRACTED,
            metadata=PaperMetadata(title=url),
            processing_time=time.time() - start,
        )

    # ── OA enrichment ─────────────────────────────────────────────────

    def _enrich_oa(self, meta: PaperMetadata) -> PaperMetadata:
        """Try Unpaywall for OA status, fall back to OpenAlex."""
        if not meta.doi:
            return meta
        # Unpaywall (primary)
        if self.config.get("contact_email"):
            data = self.api.unpaywall_check(meta.doi)
            if data:
                oa = ScholarlyAPIClient.unpaywall_oa_info(data)
                meta.oa_status = oa["status"]
                meta.oa_url = oa["url"]
                meta.license = oa.get("license")
                return meta
        # OpenAlex fallback
        oalex = self.api.openalex_lookup_doi(meta.doi)
        if oalex:
            oa_info = oalex.get("open_access", {})
            if oa_info.get("is_oa"):
                meta.oa_status = OAColor.GREEN
                meta.oa_url = oa_info.get("oa_url")
        return meta

    # ── PDF download ──────────────────────────────────────────────────

    def download_pdfs(self, results: List[ProcessingResult]) -> int:
        """Download PDFs for all results that have an OA URL. Returns count downloaded."""
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for r in results:
            if not r.metadata or not r.metadata.oa_url:
                continue
            url = r.metadata.oa_url
            safe_name = re.sub(r"[^\w\s-]", "", r.metadata.title or "paper")[:80].strip()
            filename = f"{safe_name}.pdf"
            filepath = output_dir / filename
            if filepath.exists():
                count += 1
                continue
            try:
                resp = self.api.session.get(url, timeout=self.config["timeout"], stream=True)
                content_type = resp.headers.get("content-type", "")
                if resp.status_code == 200 and ("pdf" in content_type or url.endswith(".pdf") or "arxiv.org/pdf" in url):
                    with open(filepath, "wb") as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                    logger.info(f"Downloaded: {filepath}")
                    count += 1
                else:
                    logger.warning(f"Not a PDF response for {url} (content-type: {content_type})")
            except Exception as e:
                logger.warning(f"PDF download failed for {url}: {e}")
        return count

    # ── Output ────────────────────────────────────────────────────────

    def save_results(self, results: List[ProcessingResult], filename: Optional[str] = None) -> str:
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{ts}.json"
        filepath = output_dir / filename
        with open(filepath, "w") as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        logger.info(f"Results saved to {filepath}")
        return str(filepath)

    def generate_report(self, results: List[ProcessingResult]) -> str:
        total = len(results)
        if total == 0:
            return "No results to report."
        completed = sum(1 for r in results if r.state == ProcessingState.COMPLETED)
        failed = sum(1 for r in results if r.state == ProcessingState.FAILED)
        oa_counts: Dict[str, int] = {}
        for r in results:
            if r.metadata and r.metadata.oa_status:
                key = r.metadata.oa_status.value
                oa_counts[key] = oa_counts.get(key, 0) + 1
        journal_counts: Dict[str, int] = {}
        for r in results:
            if r.metadata and r.metadata.journal:
                journal_counts[r.metadata.journal] = journal_counts.get(r.metadata.journal, 0) + 1

        lines = [
            "Academic Paper Search Report",
            "=" * 40,
            f"Total processed: {total}",
            f"Completed:       {completed}",
            f"Failed:          {failed}",
            f"Success rate:    {completed / total * 100:.0f}%",
            "",
            "Open Access Breakdown:",
        ]
        for color, count in sorted(oa_counts.items()):
            lines.append(f"  {color}: {count}")
        if journal_counts:
            lines.append("")
            lines.append("Top Journals:")
            for j, c in sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {j}: {c}")
        return "\n".join(lines)
