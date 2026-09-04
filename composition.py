"""The composition root. Nothing outside this file and function_app.py is
allowed to import from `infrastructure` directly."""
from functools import lru_cache

from application.use_cases import ProcessBlobEventUseCase
from infrastructure.azure_blob_source import AzureBlobDocumentSource
from infrastructure.cosmos_audit_logger import CosmosAuditLogger
from infrastructure.llamaindex_indexer import LlamaIndexDocumentIndexer
from infrastructure.settings import Settings


@lru_cache(maxsize=1)
def build_use_case() -> ProcessBlobEventUseCase:
    """Cached so the Function App builds each Azure client once per warm
    instance, not on every invocation."""
    settings = Settings.from_env()

    source = AzureBlobDocumentSource(account_url=settings.blob_account_url)
    indexer = LlamaIndexDocumentIndexer(
        search_endpoint=settings.search_endpoint,
        search_index_name=settings.search_index_name,
        openai_endpoint=settings.openai_endpoint,
        embedding_deployment=settings.embedding_deployment,
        embedding_dimensions=settings.embedding_dimensions,
        redis_connection_string=settings.redis_connection_string,
    )
    audit = CosmosAuditLogger(
        endpoint=settings.cosmos_endpoint,
        database_name=settings.cosmos_db_name,
        container_name=settings.cosmos_container_name,
    )
    return ProcessBlobEventUseCase(source=source, indexer=indexer, audit=audit)