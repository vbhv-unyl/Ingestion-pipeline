import hashlib
import time
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

from domain.models import IngestionResult
from domain.ports import AuditLogger


class CosmosAuditLogger(AuditLogger):
    def __init__(self, endpoint: str, database_name: str, container_name: str, credential: DefaultAzureCredential | None = None):
        client = CosmosClient(url=endpoint, credential=credential or DefaultAzureCredential())
        self._container = client.get_database_client(database_name).get_container_client(container_name)

    def record(self, result: IngestionResult) -> None:
        # Cosmos item ids can't contain '/', so a blob URL can't be used directly.
        doc_hash = hashlib.sha256(result.doc_id.encode()).hexdigest()[:16]
        self._container.upsert_item({
            "id": f"{doc_hash}-{int(time.time())}",
            "docId": result.doc_id,
            "status": result.status,
            "chunkCount": result.chunk_count,
            "error": result.error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })