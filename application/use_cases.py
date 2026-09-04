"""Business logic. Depends only on domain/ — never imports azure.* or
llama_index.* directly."""
import logging

from domain.models import BlobEvent, ChangeType, IngestionResult
from domain.ports import AuditLogger, DocumentIndexer, DocumentSource

logger = logging.getLogger(__name__)


class ProcessBlobEventUseCase:
    """The single entry point for handling one blob change end to end."""

    def __init__(self, source: DocumentSource, indexer: DocumentIndexer, audit: AuditLogger):
        self._source = source
        self._indexer = indexer
        self._audit = audit

    def execute(self, event: BlobEvent) -> IngestionResult:
        try:
            if event.change_type == ChangeType.DELETED:
                result = self._handle_delete(event.blob_url)
            else:
                result = self._handle_upsert(event.blob_url)
        except Exception as exc:
            logger.exception("Failed to process %s", event.blob_url)
            self._audit.record(IngestionResult(doc_id=event.blob_url, status="failed", error=str(exc)))
            raise  # let Durable Functions' retry policy handle retries

        self._audit.record(result)
        return result

    def _handle_upsert(self, blob_url: str) -> IngestionResult:
        raw_document = self._source.fetch(blob_url)
        chunk_count = self._indexer.index(raw_document)
        return IngestionResult(doc_id=blob_url, status="success", chunk_count=chunk_count)

    def _handle_delete(self, blob_url: str) -> IngestionResult:
        self._indexer.remove(blob_url)
        return IngestionResult(doc_id=blob_url, status="deleted", chunk_count=0)