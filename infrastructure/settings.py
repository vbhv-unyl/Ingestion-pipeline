import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    search_endpoint: str
    search_index_name: str
    openai_endpoint: str
    embedding_deployment: str
    embedding_dimensions: int
    redis_connection_string: str
    cosmos_endpoint: str
    cosmos_db_name: str
    cosmos_container_name: str
    blob_account_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            search_endpoint=os.environ["SEARCH_ENDPOINT"],
            search_index_name=os.environ.get("SEARCH_INDEX_NAME", "rag-index"),
            openai_endpoint=os.environ["OPENAI_ENDPOINT"],
            embedding_deployment=os.environ.get("EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
            embedding_dimensions=int(os.environ.get("EMBEDDING_DIMENSIONS", "3072")),
            redis_connection_string=os.environ["REDIS_CONNECTION_STRING"],
            cosmos_endpoint=os.environ["COSMOS_ENDPOINT"],
            cosmos_db_name=os.environ.get("COSMOS_DB_NAME", "ragdb"),
            cosmos_container_name=os.environ.get("COSMOS_CONTAINER_NAME", "ingestion-audit"),
            blob_account_url=os.environ["BLOB_ACCOUNT_URL"],
        )