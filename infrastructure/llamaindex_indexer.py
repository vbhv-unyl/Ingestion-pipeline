"""Concrete DocumentIndexer implementation — the only file in the project
that imports llama_index. Swapping frameworks later means changing this file alone."""
import os
import tempfile

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionCache, IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.storage.kvstore.redis import RedisKVStore
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore

from domain.models import RawDocument
from domain.ports import DocumentIndexer


class LlamaIndexDocumentIndexer(DocumentIndexer):
    def __init__(
        self, search_endpoint: str, search_index_name: str, openai_endpoint: str,
        embedding_deployment: str, embedding_dimensions: int, redis_connection_string: str,
        credential: DefaultAzureCredential | None = None,
    ):
        credential = credential or DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        embed_model = AzureOpenAIEmbedding(
            deployment_name=embedding_deployment, azure_endpoint=openai_endpoint,
            azure_ad_token_provider=token_provider, api_version="2024-06-01",
        )
        search_client = SearchClient(endpoint=search_endpoint, index_name=search_index_name, credential=credential)

        self._vector_store = AzureAISearchVectorStore(
            search_or_index_client=search_client, index_name=search_index_name,
            embedding_dimensionality=embedding_dimensions, id_field_key="id",
            chunk_field_key="content", embedding_field_key="content_vector",
            metadata_string_field_key="metadata", doc_id_field_key="doc_id",
        )

        kv_store = RedisKVStore(redis_url=redis_connection_string)
        self._docstore = RedisDocumentStore(redis_kvstore=kv_store, namespace="rag-ingestion")
        cache = IngestionCache(cache=kv_store, collection="rag-ingestion-cache")

        self._pipeline = IngestionPipeline(
            transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=64), embed_model],
            docstore=self._docstore, docstore_strategy="upserts_and_delete",
            vector_store=self._vector_store, cache=cache,
        )

    def index(self, document: RawDocument) -> int:
        documents = self._to_llamaindex_documents(document)
        nodes = self._pipeline.run(documents=documents)
        return len(nodes)

    def remove(self, doc_id: str) -> None:
        self._vector_store.delete(ref_doc_id=doc_id)
        self._docstore.delete_ref_doc(doc_id, raise_error=False)

    @staticmethod
    def _to_llamaindex_documents(document: RawDocument):
        suffix = os.path.splitext(document.file_name)[1] or ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(document.content)
            tmp_path = tmp.name
        try:
            docs = SimpleDirectoryReader(input_files=[tmp_path]).load_data()
        finally:
            os.remove(tmp_path)

        for doc in docs:
            doc.id_ = document.source_url  # ref_doc_id used for dedup/upsert/delete matching
            doc.metadata.update({
                "blob_path": document.source_url,
                "content_hash": document.content_hash,
                "last_modified": document.last_modified.isoformat(),
            })
        return docs