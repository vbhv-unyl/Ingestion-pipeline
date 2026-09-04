"""Concrete DocumentSource implementation backed by Azure Blob Storage."""
import hashlib
from urllib.parse import unquote, urlparse

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from domain.models import RawDocument
from domain.ports import DocumentSource


class AzureBlobDocumentSource(DocumentSource):
    def __init__(self, account_url: str, credential: DefaultAzureCredential | None = None):
        self._client = BlobServiceClient(account_url=account_url, credential=credential or DefaultAzureCredential())

    def fetch(self, blob_url: str) -> RawDocument:
        container_name, blob_name = self._parse(blob_url)
        blob_client = self._client.get_blob_client(container=container_name, blob=blob_name)
        properties = blob_client.get_blob_properties()
        data = blob_client.download_blob().readall()

        return RawDocument(
            source_url=blob_url,
            content=data,
            content_hash=hashlib.sha256(data).hexdigest(),
            last_modified=properties.last_modified,
            file_name=blob_name,
        )

    @staticmethod
    def _parse(blob_url: str) -> tuple[str, str]:
        parsed = urlparse(blob_url)
        container_name, blob_name = parsed.path.lstrip("/").split("/", 1)
        return container_name, unquote(blob_name)