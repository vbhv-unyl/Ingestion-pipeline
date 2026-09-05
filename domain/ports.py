"""Abstract contracts the application layer depends on. Infrastructure
implementations plug into these interfaces — never the other way around."""
from abc import ABC, abstractmethod

from domain.models import IngestionResult, RawDocument


class DocumentSource(ABC):
    """Knows how to fetch raw bytes for a single document, given its URL."""

    @abstractmethod
    def fetch(self, blob_url: str) -> RawDocument: ...


class DocumentIndexer(ABC):
    """Knows how to parse+chunk+embed+upsert a document into a vector index,
    and how to remove one when it's deleted."""

    @abstractmethod
    def index(self, document: RawDocument) -> int:
        """Returns the number of chunks written."""

    @abstractmethod
    def remove(self, doc_id: str) -> None: ...


class AuditLogger(ABC):
    """Knows how to persist a human-queryable record of what happened."""

    @abstractmethod
    def record(self, result: IngestionResult) -> None: ...