#!/usr/bin/env python3
"""
Academic Paper Search Framework
A modular, AI-driven framework for autonomous identification and retrieval of open access scholarly literature.
"""

import json
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import yaml
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingState(Enum):
    """States in the processing pipeline"""
    NEW = "new"
    TRIAGED = "triaged"
    CLASSIFIED_AS_PAPER = "classified_as_paper"
    METADATA_EXTRACTED = "metadata_extracted"
    OA_STATUS_VERIFIED = "oa_status_verified"
    RETRIEVAL_PENDING = "retrieval_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_OA_CHECK = "retry_oa_check"

class OAColor(Enum):
    """Open Access color classifications"""
    GOLD = "gold"
    GREEN = "green"
    HYBRID = "hybrid"
    BRONZE = "bronze"
    CLOSED = "closed"

@dataclass
class PaperMetadata:
    """Structured metadata for a scholarly paper"""
    title: str
    authors: List[str]
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = None
    oa_status: Optional[OAColor] = None
    oa_url: Optional[str] = None
    license: Optional[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class ProcessingResult:
    """Result of processing a URL through the pipeline"""
    url: str
    state: ProcessingState
    metadata: Optional[PaperMetadata] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0

class LLMClient:
    """Abstract LLM client interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup the LLM client - to be implemented by subclasses"""
        pass
    
    def extract_metadata(self, text_content: str, title: str, authors: List[str], doi: str, abstract: str) -> Optional[PaperMetadata]:
        """Extract enhanced metadata using LLM - to be implemented by subclasses"""
        pass

class OllamaClient(LLMClient):
    """Ollama LLM client for local model inference"""
    
    def _setup_client(self):
        """Setup Ollama client"""
        self.base_url = self.config.get('ollama_base_url', 'http://localhost:11434')
        self.model = self.config.get('ollama_model', 'llama2')
        self.timeout = self.config.get('ollama_timeout', 30)
    
    def extract_metadata(self, text_content: str, title: str, authors: List[str], doi: str, abstract: str) -> Optional[PaperMetadata]:
        """Extract enhanced metadata using Ollama"""
        try:
            # Create prompt for Ollama
            prompt = f"""
Extract scholarly paper metadata from the following content:

Title: {title}
Authors: {', '.join(authors)}
DOI: {doi}
Abstract: {abstract}

Content: {text_content[:4000]}

Return a JSON object with the following structure:
{{
    "title": "full paper title",
    "authors": ["author1", "author2"],
    "doi": "doi if found",
    "arxiv_id": "arxiv id if found",
    "publication_year": 2023,
    "journal": "journal name",
    "abstract": "paper abstract",
    "keywords": ["keyword1", "keyword2"]
}}

Return only the JSON object, no additional text.
"""
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            llm_response = result.get('response', '').strip()
            
            # Clean up response (remove markdown if present)
            if '```json' in llm_response:
                llm_response = llm_response.split('```json')[1].split('```')[0]
            elif '```' in llm_response:
                llm_response = llm_response.split('```')[1]
            
            # Parse JSON
            llm_data = json.loads(llm_response)
            
            return PaperMetadata(
                title=llm_data.get('title', title),
                authors=llm_data.get('authors', authors),
                doi=llm_data.get('doi', doi),
                arxiv_id=llm_data.get('arxiv_id'),
                publication_year=llm_data.get('publication_year'),
                journal=llm_data.get('journal'),
                abstract=llm_data.get('abstract', abstract),
                keywords=llm_data.get('keywords', [])
            )
            
        except Exception as e:
            logger.error(f"Ollama metadata extraction failed: {e}")
            return None

class OpenAIClient(LLMClient):
    """OpenAI LLM client for cloud model inference"""
    
    def _setup_client(self):
        """Setup OpenAI client"""
        try:
            import openai
            openai.api_key = self.config.get('openai_api_key')
            self.client = openai
            self.model = self.config.get('openai_model', 'gpt-4')
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
            self.client = None
    
    def extract_metadata(self, text_content: str, title: str, authors: List[str], doi: str, abstract: str) -> Optional[PaperMetadata]:
        """Extract enhanced metadata using OpenAI"""
        if not self.client:
            return None
        
        try:
            prompt = f"""
Extract scholarly paper metadata from the following content:

Title: {title}
Authors: {', '.join(authors)}
DOI: {doi}
Abstract: {abstract}

Content: {text_content[:4000]}

Return a JSON object with the following structure:
{{
    "title": "full paper title",
    "authors": ["author1", "author2"],
    "doi": "doi if found",
    "arxiv_id": "arxiv id if found",
    "publication_year": 2023,
    "journal": "journal name",
    "abstract": "paper abstract",
    "keywords": ["keyword1", "keyword2"]
}}
"""
            
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse LLM response
            llm_data = json.loads(response.choices[0].message.content)
            
            return PaperMetadata(
                title=llm_data.get('title', title),
                authors=llm_data.get('authors', authors),
                doi=llm_data.get('doi', doi),
                arxiv_id=llm_data.get('arxiv_id'),
                publication_year=llm_data.get('publication_year'),
                journal=llm_data.get('journal'),
                abstract=llm_data.get('abstract', abstract),
                keywords=llm_data.get('keywords', [])
            )
            
        except Exception as e:
            logger.error(f"OpenAI metadata extraction failed: {e}")
            return None

class AcademicPaperFramework:
    """
    Main framework class implementing the modular, state-driven architecture
    for autonomous scholarly literature retrieval.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the framework with configuration"""
        self.config = self._load_config(config_path)
        self.results = []
        self.session = requests.Session()
        self._setup_session()
        self._setup_llm_client()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'rate_limit_per_second': 1,
            'max_retries': 3,
            'timeout': 30,
            'user_agent': 'AcademicPaperFramework/1.0 (research-agent)',
            'output_dir': 'results',
            'save_pdfs': True,
            'topics_of_interest': [],
            'paper_lists': [],
            'enable_llm_enhancement': False,
            'llm_provider': 'ollama',  # 'ollama' or 'openai'
            'ollama_base_url': 'http://localhost:11434',
            'ollama_model': 'llama2',
            'ollama_timeout': 30,
            'openai_api_key': None,
            'openai_model': 'gpt-4'
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _setup_session(self):
        """Configure the requests session with proper headers and rate limiting"""
        self.session.headers.update({
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _setup_llm_client(self):
        """Setup LLM client based on configuration"""
        self.llm_client = None
        
        if not self.config.get('enable_llm_enhancement'):
            return
        
        provider = self.config.get('llm_provider', 'ollama')
        
        if provider == 'ollama':
            try:
                self.llm_client = OllamaClient(self.config)
                logger.info(f"Ollama client initialized with model: {self.config.get('ollama_model')}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
        
        elif provider == 'openai':
            try:
                self.llm_client = OpenAIClient(self.config)
                logger.info(f"OpenAI client initialized with model: {self.config.get('openai_model')}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def search_ad_hoc(self, query: str, max_results: int = 50) -> List[ProcessingResult]:
        """
        Perform an ad-hoc search for papers based on a query string.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of ProcessingResult objects
        """
        logger.info(f"Starting ad-hoc search for: {query}")
        
        # Search across multiple sources
        urls = []
        
        # Search arXiv
        arxiv_urls = self._search_arxiv(query, max_results // 3)
        urls.extend(arxiv_urls)
        
        # Search Crossref
        crossref_urls = self._search_crossref(query, max_results // 3)
        urls.extend(crossref_urls)
        
        # Search PubMed Central
        pmc_urls = self._search_pmc(query, max_results // 3)
        urls.extend(pmc_urls)
        
        # Process all URLs through the pipeline
        results = []
        for url in urls[:max_results]:
            result = self.process_url(url)
            if result.state in [ProcessingState.COMPLETED, ProcessingState.METADATA_EXTRACTED]:
                results.append(result)
        
        return results
    
    def search_by_topics(self, topics: List[str], max_results_per_topic: int = 20) -> List[ProcessingResult]:
        """
        Search for papers based on configured topics of interest.
        
        Args:
            topics: List of topics to search for
            max_results_per_topic: Maximum results per topic
            
        Returns:
            List of ProcessingResult objects
        """
        logger.info(f"Starting topic-based search for: {topics}")
        
        all_results = []
        for topic in topics:
            logger.info(f"Searching for topic: {topic}")
            results = self.search_ad_hoc(topic, max_results_per_topic)
            all_results.extend(results)
        
        return all_results
    
    def process_paper_list(self, paper_list_path: str) -> List[ProcessingResult]:
        """
        Process a list of papers from a file (e.g., your mineral exploration readme).
        
        Args:
            paper_list_path: Path to file containing paper URLs or DOIs
            
        Returns:
            List of ProcessingResult objects
        """
        logger.info(f"Processing paper list from: {paper_list_path}")
        
        urls = self._load_paper_list(paper_list_path)
        results = []
        
        for url in urls:
            result = self.process_url(url)
            results.append(result)
        
        return results
    
    def _load_paper_list(self, file_path: str) -> List[str]:
        """Load paper URLs/DOIs from various file formats"""
        urls = []
        
        if not os.path.exists(file_path):
            logger.error(f"Paper list file not found: {file_path}")
            return urls
        
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Try to parse as different formats
            if file_path.endswith('.json'):
                data = json.loads(content)
                urls = self._extract_urls_from_json(data)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(content)
                urls = self._extract_urls_from_yaml(data)
            else:
                # Assume plain text with URLs/DOIs
                urls = self._extract_urls_from_text(content)
        
        return urls
    
    def _extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs and DOIs from plain text"""
        urls = []
        
        # Extract DOIs
        doi_pattern = r'10\.\d{4,9}/[-._;()/:\w]+'
        dois = re.findall(doi_pattern, text)
        urls.extend([f"https://doi.org/{doi}" for doi in dois])
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"]+'
        urls.extend(re.findall(url_pattern, text))
        
        return list(set(urls))  # Remove duplicates
    
    def _extract_urls_from_json(self, data: Any) -> List[str]:
        """Extract URLs from JSON structure"""
        urls = []
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['url', 'doi', 'link'] and isinstance(value, str):
                        if value.startswith('10.'):
                            urls.append(f"https://doi.org/{value}")
                        elif value.startswith('http'):
                            urls.append(value)
                    else:
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(data)
        return list(set(urls))
    
    def _extract_urls_from_yaml(self, data: Any) -> List[str]:
        """Extract URLs from YAML structure"""
        return self._extract_urls_from_json(data)
    
    def process_url(self, url: str) -> ProcessingResult:
        """
        Process a single URL through the complete pipeline.
        
        Args:
            url: URL to process
            
        Returns:
            ProcessingResult object
        """
        start_time = time.time()
        result = ProcessingResult(url=url, state=ProcessingState.NEW)
        
        try:
            # Module 1: URL Ingestion and Content Triage
            if not self._triage_url(url):
                result.state = ProcessingState.FAILED
                result.error_message = "Failed triage - not a scholarly resource"
                return result
            
            result.state = ProcessingState.TRIAGED
            
            # Module 2: Scholarly Content Identification and Metadata Extraction
            metadata = self._extract_metadata(url)
            if not metadata:
                result.state = ProcessingState.FAILED
                result.error_message = "Failed to extract metadata"
                return result
            
            result.metadata = metadata
            result.state = ProcessingState.METADATA_EXTRACTED
            
            # Module 3: Open Access Status Verification
            oa_status = self._verify_oa_status(metadata)
            if oa_status:
                result.metadata.oa_status = oa_status['status']
                result.metadata.oa_url = oa_status.get('url')
                result.state = ProcessingState.OA_STATUS_VERIFIED
            else:
                result.state = ProcessingState.FAILED
                result.error_message = "Failed to verify OA status"
                return result
            
            # Module 4: Conditional and Compliant PDF Retrieval
            if self.config.get('save_pdfs') and result.metadata.oa_url:
                pdf_path = self._retrieve_pdf(result.metadata.oa_url, result.metadata)
                if pdf_path:
                    result.state = ProcessingState.COMPLETED
                else:
                    result.state = ProcessingState.FAILED
                    result.error_message = "Failed to retrieve PDF"
            else:
                result.state = ProcessingState.COMPLETED
            
        except Exception as e:
            result.state = ProcessingState.FAILED
            result.error_message = str(e)
            logger.error(f"Error processing {url}: {e}")
        
        result.processing_time = time.time() - start_time
        return result
    
    def _triage_url(self, url: str) -> bool:
        """Module 1: URL Ingestion and Content Triage"""
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Check for scholarly domains
            scholarly_domains = [
                'arxiv.org', 'biorxiv.org', 'doi.org', 'crossref.org',
                'pubmed.ncbi.nlm.nih.gov', 'pmc.ncbi.nlm.nih.gov',
                'scholar.google.com', 'researchgate.net', 'academia.edu'
            ]
            
            if not any(domain in url for domain in scholarly_domains):
                return False
            
            # Check content type
            response = self.session.head(url, timeout=self.config['timeout'])
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' not in content_type and 'application/pdf' not in content_type:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Triage failed for {url}: {e}")
            return False
    
    def _extract_metadata(self, url: str) -> Optional[PaperMetadata]:
        """Module 2: Scholarly Content Identification and Metadata Extraction"""
        try:
            # Fetch page content
            response = self.session.get(url, timeout=self.config['timeout'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic metadata using heuristics
            title = self._extract_title(soup)
            authors = self._extract_authors(soup)
            doi = self._extract_doi(soup, url)
            abstract = self._extract_abstract(soup)
            
            if not title:
                return None
            
            # Use LLM for enhanced extraction if available
            if self.llm_client:
                enhanced_metadata = self.llm_client.extract_metadata(
                    soup.get_text(), title, authors, doi or '', abstract or ''
                )
                if enhanced_metadata:
                    return enhanced_metadata
            
            return PaperMetadata(
                title=title,
                authors=authors,
                doi=doi,
                abstract=abstract
            )
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract paper title from HTML"""
        # Try multiple selectors for title
        title_selectors = [
            'h1',
            '.title',
            '.paper-title',
            'meta[name="citation_title"]',
            'meta[property="og:title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return None
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract author names from HTML"""
        authors = []
        
        # Try multiple approaches
        author_selectors = [
            '.authors',
            '.author',
            'meta[name="citation_author"]',
            '.byline'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.name == 'meta':
                    authors.append(element.get('content', '').strip())
                else:
                    authors.append(element.get_text().strip())
        
        return [author for author in authors if author]
    
    def _extract_doi(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract DOI from HTML or URL"""
        # Check HTML for DOI
        doi_pattern = r'10\.\d{4,9}/[-._;()/:\w]+'
        
        # Check meta tags
        doi_meta = soup.find('meta', {'name': 'citation_doi'})
        if doi_meta:
            return doi_meta.get('content')
        
        # Check text content
        text = soup.get_text()
        doi_match = re.search(doi_pattern, text)
        if doi_match:
            return doi_match.group()
        
        # Check URL
        doi_match = re.search(doi_pattern, url)
        if doi_match:
            return doi_match.group()
        
        return None
    
    def _extract_abstract(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract abstract from HTML"""
        abstract_selectors = [
            '.abstract',
            '.summary',
            'meta[name="description"]',
            'meta[property="og:description"]'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return None
    
    def _verify_oa_status(self, metadata: PaperMetadata) -> Optional[Dict[str, Any]]:
        """Module 3: Open Access Status Verification"""
        if not metadata.doi:
            return None
        
        try:
            # For now, return a basic OA status
            # In a full implementation, this would query Unpaywall, Crossref, etc.
            return {
                'status': OAColor.GREEN,  # Assume green OA for now
                'url': f"https://doi.org/{metadata.doi}"
            }
            
        except Exception as e:
            logger.error(f"OA status verification failed for {metadata.doi}: {e}")
            return None
    
    def _retrieve_pdf(self, url: str, metadata: PaperMetadata) -> Optional[str]:
        """Module 4: Conditional and Compliant PDF Retrieval"""
        try:
            # Create output directory
            output_dir = Path(self.config['output_dir'])
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            safe_title = re.sub(r'[^\w\s-]', '', metadata.title)[:100]
            filename = f"{safe_title}_{metadata.doi or 'unknown'}.pdf"
            filepath = output_dir / filename
            
            # Download PDF
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"PDF saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"PDF retrieval failed for {url}: {e}")
            return None
    
    def _search_arxiv(self, query: str, max_results: int) -> List[str]:
        """Search arXiv for papers"""
        urls = []
        try:
            # Use arXiv API
            api_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            response = self.session.get(api_url, params=params)
            soup = BeautifulSoup(response.content, 'xml')
            
            for entry in soup.find_all('entry'):
                url = entry.find('id')
                if url:
                    urls.append(url.text)
        
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
        
        return urls
    
    def _search_crossref(self, query: str, max_results: int) -> List[str]:
        """Search Crossref for papers"""
        urls = []
        try:
            # Basic Crossref search using their API
            api_url = "https://api.crossref.org/works"
            params = {
                'query': query,
                'rows': max_results,
                'sort': 'relevance'
            }
            
            response = self.session.get(api_url, params=params)
            data = response.json()
            
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    doi = item.get('DOI')
                    if doi:
                        urls.append(f"https://doi.org/{doi}")
        
        except Exception as e:
            logger.error(f"Crossref search failed: {e}")
        
        return urls
    
    def _search_pmc(self, query: str, max_results: int) -> List[str]:
        """Search PubMed Central for papers"""
        urls = []
        try:
            # Use PMC API
            api_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                'db': 'pmc',
                'term': query,
                'retmax': max_results,
                'retmode': 'json'
            }
            
            response = self.session.get(api_url, params=params)
            data = response.json()
            
            if 'esearchresult' in data:
                ids = data['esearchresult'].get('idlist', [])
                for pmcid in ids:
                    urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/")
        
        except Exception as e:
            logger.error(f"PMC search failed: {e}")
        
        return urls
    
    def save_results(self, results: List[ProcessingResult], filename: Optional[str] = None) -> str:
        """Save processing results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"academic_paper_results_{timestamp}.json"
        
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            result_dict = {
                'url': result.url,
                'state': result.state.value,
                'processing_time': result.processing_time,
                'retry_count': result.retry_count,
                'error_message': result.error_message
            }
            
            if result.metadata:
                result_dict['metadata'] = asdict(result.metadata)
                if result.metadata.oa_status:
                    result_dict['metadata']['oa_status'] = result.metadata.oa_status.value
            
            serializable_results.append(result_dict)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        return str(filepath)
    
    def generate_report(self, results: List[ProcessingResult]) -> str:
        """Generate a summary report of processing results"""
        total = len(results)
        completed = len([r for r in results if r.state == ProcessingState.COMPLETED])
        failed = len([r for r in results if r.state == ProcessingState.FAILED])
        
        oa_papers = [r for r in results if r.metadata and r.metadata.oa_status]
        gold_oa = len([r for r in oa_papers if r.metadata.oa_status == OAColor.GOLD])
        green_oa = len([r for r in oa_papers if r.metadata.oa_status == OAColor.GREEN])
        
        report = f"""
Academic Paper Search Report
===========================

Total URLs Processed: {total}
Successfully Completed: {completed}
Failed: {failed}
Success Rate: {(completed/total*100):.1f}%

Open Access Breakdown:
- Gold OA: {gold_oa}
- Green OA: {green_oa}
- Total OA Papers: {len(oa_papers)}

Processing Time:
- Average: {sum(r.processing_time for r in results)/total:.2f}s
- Total: {sum(r.processing_time for r in results):.2f}s

LLM Enhancement: {'Enabled' if self.llm_client else 'Disabled'}
LLM Provider: {self.config.get('llm_provider', 'None')}

Top Journals:
"""
        
        # Count journals
        journal_counts = {}
        for result in results:
            if result.metadata and result.metadata.journal:
                journal_counts[result.metadata.journal] = journal_counts.get(result.metadata.journal, 0) + 1
        
        for journal, count in sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"- {journal}: {count}\n"
        
        return report 