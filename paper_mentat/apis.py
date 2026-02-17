"""API clients for scholarly data sources: Crossref, Unpaywall, OpenAlex, arXiv, PubMed."""

import re
import logging
import time
from typing import Dict, List, Optional, Any
from xml.etree import ElementTree

import requests

from .models import PaperMetadata, OAColor

logger = logging.getLogger(__name__)


class ScholarlyAPIClient:
    """Unified client for Crossref, Unpaywall, OpenAlex, arXiv, and PubMed APIs."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        ua = config.get("user_agent", "AcademicPaperFramework/1.0 (research-agent)")
        self.session.headers.update({"User-Agent": ua})
        self.session.verify = config.get("ssl_verify", True)
        self.email = config.get("contact_email", "")
        self.rate_delay = 1.0 / max(config.get("rate_limit_per_second", 1), 0.1)
        self.timeout = config.get("timeout", 30)
        self._last_request_time = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        self._throttle()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None

    # ── Crossref ──────────────────────────────────────────────────────

    def crossref_search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search Crossref for works matching a query. Returns list of work items."""
        params = {"query": query, "rows": max_results, "sort": "relevance"}
        if self.email:
            params["mailto"] = self.email
        resp = self._get("https://api.crossref.org/works", params)
        if not resp:
            return []
        data = resp.json()
        return data.get("message", {}).get("items", [])

    def crossref_lookup_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Look up a single DOI via Crossref."""
        params = {}
        if self.email:
            params["mailto"] = self.email
        resp = self._get(f"https://api.crossref.org/works/{doi}", params or None)
        if not resp:
            return None
        return resp.json().get("message")

    @staticmethod
    def crossref_to_metadata(item: Dict[str, Any]) -> PaperMetadata:
        """Convert a Crossref work item to PaperMetadata."""
        title_list = item.get("title", [])
        title = title_list[0] if title_list else "Unknown"
        # Skip non-article types (figures, components, etc.)
        doi = item.get("DOI", "")
        if re.search(r"/fig-\d+|/table-\d+|/supp-\d+", doi):
            return None
        authors = []
        for a in item.get("author", []):
            name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if name:
                authors.append(name)
        year = None
        for date_field in ("published-print", "published-online", "created"):
            parts = item.get(date_field, {}).get("date-parts", [[]])
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        journal_list = item.get("container-title", [])
        abstract = item.get("abstract", "")
        # Strip JATS XML tags from abstract
        if abstract:
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
        return PaperMetadata(
            title=title,
            authors=authors,
            doi=item.get("DOI"),
            publication_year=year,
            journal=journal_list[0] if journal_list else None,
            abstract=abstract or None,
        )

    # ── Unpaywall ─────────────────────────────────────────────────────

    def unpaywall_check(self, doi: str) -> Optional[Dict[str, Any]]:
        """Check OA status via Unpaywall. Returns the raw API response dict."""
        if not self.email:
            logger.warning("Unpaywall requires contact_email in config")
            return None
        resp = self._get(f"https://api.unpaywall.org/v2/{doi}", {"email": self.email})
        if not resp:
            return None
        return resp.json()

    @staticmethod
    def unpaywall_oa_info(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract OA color and best URL from Unpaywall response."""
        is_oa = data.get("is_oa", False)
        if not is_oa:
            return {"status": OAColor.CLOSED, "url": None, "license": None}

        status_map = {
            "gold": OAColor.GOLD,
            "green": OAColor.GREEN,
            "hybrid": OAColor.HYBRID,
            "bronze": OAColor.BRONZE,
        }
        oa_color = status_map.get(data.get("oa_status", ""), OAColor.UNKNOWN)
        best = data.get("best_oa_location") or {}
        return {
            "status": oa_color,
            "url": best.get("url_for_pdf") or best.get("url"),
            "license": best.get("license"),
        }

    # ── OpenAlex ──────────────────────────────────────────────────────

    def openalex_search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search OpenAlex for works."""
        params = {"search": query, "per_page": min(max_results, 200)}
        if self.email:
            params["mailto"] = self.email
        resp = self._get("https://api.openalex.org/works", params)
        if not resp:
            return []
        return resp.json().get("results", [])

    def openalex_lookup_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Look up a DOI via OpenAlex."""
        params = {}
        if self.email:
            params["mailto"] = self.email
        resp = self._get(f"https://api.openalex.org/works/doi:{doi}", params or None)
        if not resp:
            return None
        return resp.json()

    @staticmethod
    def openalex_to_metadata(item: Dict[str, Any]) -> PaperMetadata:
        """Convert an OpenAlex work to PaperMetadata."""
        title = item.get("title") or "Unknown"
        authors = []
        for authorship in item.get("authorships", []):
            name = authorship.get("author", {}).get("display_name")
            if name:
                authors.append(name)
        year = item.get("publication_year")
        # Primary location for journal
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        journal = source.get("display_name")
        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        # OA info from OpenAlex (derived from Unpaywall)
        oa = item.get("open_access", {})
        oa_url = oa.get("oa_url")
        oa_status = None
        if oa.get("is_oa"):
            oa_status = OAColor.GREEN  # conservative default
        return PaperMetadata(
            title=title,
            authors=authors,
            doi=doi,
            publication_year=year,
            journal=journal,
            oa_status=oa_status,
            oa_url=oa_url,
        )

    # ── arXiv ─────────────────────────────────────────────────────────

    def arxiv_search(self, query: str, max_results: int = 20) -> List[PaperMetadata]:
        """Search arXiv and return parsed metadata."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        resp = self._get("http://export.arxiv.org/api/query", params)
        if not resp:
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        try:
            root = ElementTree.fromstring(resp.content)
        except ElementTree.ParseError:
            logger.warning("Failed to parse arXiv XML response")
            return []

        results = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            title = title_el.text.strip().replace("\n", " ") if title_el is not None else "Unknown"
            authors = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None:
                    authors.append(name_el.text.strip())
            summary_el = entry.find("atom:summary", ns)
            abstract = summary_el.text.strip() if summary_el is not None else None
            id_el = entry.find("atom:id", ns)
            arxiv_url = id_el.text.strip() if id_el is not None else ""
            # Extract arXiv ID from URL like http://arxiv.org/abs/2301.12345v1
            arxiv_id = None
            m = re.search(r"arxiv\.org/abs/(.+)", arxiv_url)
            if m:
                arxiv_id = m.group(1)
            published_el = entry.find("atom:published", ns)
            year = None
            if published_el is not None:
                try:
                    year = int(published_el.text[:4])
                except (ValueError, TypeError):
                    pass
            pdf_url = arxiv_url.replace("/abs/", "/pdf/") if arxiv_url else None
            results.append(PaperMetadata(
                title=title,
                authors=authors,
                arxiv_id=arxiv_id,
                publication_year=year,
                abstract=abstract,
                oa_status=OAColor.GREEN,
                oa_url=pdf_url,
            ))
        return results

    # ── CORE.ac.uk ─────────────────────────────────────────────────────

    def core_search(self, query: str, max_results: int = 20) -> List[PaperMetadata]:
        """Search CORE.ac.uk full text index. Requires core_api_key in config."""
        api_key = self.config.get("core_api_key")
        if not api_key:
            logger.warning("core_api_key not set in config, skipping CORE search")
            return []
        # Wrap multi-word queries in quotes with proximity slop for phrase-like matching
        if " " in query and not (query.startswith('"') or ":" in query):
            query = f'"{query}"~10'  # words within 10 positions of each other
        params = {"q": query, "limit": min(max_results, 100), "sort": "relevance"}
        self._throttle()
        try:
            resp = self.session.get(
                "https://api.core.ac.uk/v3/search/works",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"CORE search failed: {e}")
            return []
        data = resp.json()
        results = []
        for item in data.get("results", []):
            dl_url = item.get("downloadUrl") or item.get("sourceFulltextUrls")
            if isinstance(dl_url, list):
                dl_url = dl_url[0] if dl_url else None
            results.append(PaperMetadata(
                title=item.get("title", "Unknown"),
                authors=[a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)],
                doi=item.get("doi"),
                publication_year=item.get("yearPublished"),
                journal=item.get("publisher"),
                abstract=item.get("abstract"),
                oa_status=OAColor.GREEN if dl_url else None,
                oa_url=dl_url,
            ))
        return results

    # ── PubMed Central ────────────────────────────────────────────────

    def pmc_search(self, query: str, max_results: int = 20) -> List[str]:
        """Search PubMed Central, return list of PMC article URLs."""
        params = {
            "db": "pmc",
            "term": f"{query} open access[filter]",
            "retmax": max_results,
            "retmode": "json",
        }
        resp = self._get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params)
        if not resp:
            return []
        data = resp.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        return [f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/" for pmcid in ids]
