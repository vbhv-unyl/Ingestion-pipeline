"""Framework-agnostic data structures. No Azure SDK, no LlamaIndex imports here —
this layer should be able to be copy-pasted into a completely different project
and still compile."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    CREATED_OR_UPDATED = "created_or_updated"
    DELETED = "deleted"


@dataclass(frozen=True)
class BlobEvent:
    """A normalized 'something changed in blob storage' event, independent of
    whether it arrived via Event Grid, a queue message, or a manual backfill."""
    blob_url: str
    change_type: ChangeType


@dataclass
class RawDocument:
    """Raw bytes pulled from storage, before any parsing/chunking happens."""
    source_url: str
    content: bytes
    content_hash: str
    last_modified: datetime
    file_name: str


@dataclass
class IngestionResult:
    doc_id: str
    status: str  # "success" | "deleted" | "failed"
    chunk_count: int = 0
    error: str | None = None
