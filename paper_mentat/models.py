"""Data models for the academic paper framework."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Any, Dict


class ProcessingState(Enum):
    NEW = "new"
    TRIAGED = "triaged"
    METADATA_EXTRACTED = "metadata_extracted"
    OA_VERIFIED = "oa_verified"
    COMPLETED = "completed"
    FAILED = "failed"


class OAColor(Enum):
    GOLD = "gold"
    GREEN = "green"
    HYBRID = "hybrid"
    BRONZE = "bronze"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass
class PaperMetadata:
    title: str
    authors: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    oa_status: Optional[OAColor] = None
    oa_url: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.oa_status:
            d["oa_status"] = self.oa_status.value
        return d


@dataclass
class ProcessingResult:
    url: str
    state: ProcessingState = ProcessingState.NEW
    metadata: Optional[PaperMetadata] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "url": self.url,
            "state": self.state.value,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
        }
        if self.metadata:
            d["metadata"] = self.metadata.to_dict()
        return d
