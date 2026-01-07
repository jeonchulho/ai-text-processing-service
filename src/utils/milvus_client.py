"""
Milvus client for vector storage and similarity search.

This module provides a wrapper around Milvus for storing and
searching text embeddings for translation and document chunks.
"""

from typing import List, Dict, Optional, Any
import structlog
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema,
    DataType, utility
)

from src.core.config import settings
from src.core.exceptions import VectorStoreError

logger = structlog.get_logger(__name__)


class MilvusClient:
    """Milvus client wrapper for vector operations."""

    def __init__(self):
        """Initialize Milvus client and connect to server."""
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                timeout=10
            )
            logger.info("Milvus client initialized successfully")
            self._ensure_collections()
        except Exception as e:
            logger.error(f"Failed to initialize Milvus client: {e}")
            raise VectorStoreError(f"Milvus connection failed: {e}")

    def _ensure_collections(self):
        """Ensure required collections exist."""
        collections_config = {
            "translations": {
                "description": "Translation embeddings for similarity search",
                "dim": 1536  # OpenAI ada-002 dimension
            },
            "document_chunks": {
                "description": "Document chunk embeddings for summarization",
                "dim": 1536
            },
            "summaries": {
                "description": "Summary embeddings for retrieval",
                "dim": 1536
            }
        }

        for name, config in collections_config.items():
            if not utility.has_collection(name):
                self._create_collection(name, config["description"], config["dim"])
            else:
                logger.info(f"Collection {name} already exists")

    def _create_collection(
        self,
        name: str,
        description: str,
        dim: int = 1536
    ):
        """
        Create a new collection.

        Args:
            name: Collection name
            description: Collection description
            dim: Embedding dimension
        """
        try:
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
            ]

            schema = CollectionSchema(
                fields=fields,
                description=description
            )

            collection = Collection(name=name, schema=schema)

            # Create index for vector field
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )

            logger.info(f"Created collection: {name}")
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise VectorStoreError(f"Collection creation failed: {e}")

    def insert(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Insert embeddings into a collection.

        Args:
            collection_name: Name of the collection
            embeddings: List of embedding vectors
            texts: List of text strings
            metadata: Optional list of metadata dictionaries

        Returns:
            List of inserted IDs
        """
        try:
            collection = Collection(collection_name)

            if metadata is None:
                metadata = [{}] * len(embeddings)

            # Convert metadata to JSON strings
            import json
            metadata_strings = [json.dumps(m) for m in metadata]

            entities = [
                embeddings,
                texts,
                metadata_strings
            ]

            result = collection.insert(entities)
            collection.flush()

            logger.info(f"Inserted {len(embeddings)} vectors into {collection_name}")
            return result.primary_keys

        except Exception as e:
            logger.error(f"Failed to insert into {collection_name}: {e}")
            raise VectorStoreError(f"Insert operation failed: {e}")

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_expr: Optional filter expression

        Returns:
            List of search results with text and metadata
        """
        try:
            collection = Collection(collection_name)
            collection.load()

            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }

            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["text", "metadata"]
            )

            # Format results
            formatted_results = []
            import json
            for hit in results[0]:
                formatted_results.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "text": hit.entity.get("text"),
                    "metadata": json.loads(hit.entity.get("metadata", "{}"))
                })

            logger.info(f"Search in {collection_name} returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise VectorStoreError(f"Search operation failed: {e}")

    def delete(
        self,
        collection_name: str,
        ids: List[int]
    ) -> bool:
        """
        Delete vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of IDs to delete

        Returns:
            True if successful
        """
        try:
            collection = Collection(collection_name)
            expr = f"id in {ids}"
            collection.delete(expr)
            collection.flush()

            logger.info(f"Deleted {len(ids)} vectors from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from {collection_name}: {e}")
            raise VectorStoreError(f"Delete operation failed: {e}")

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = Collection(collection_name)
            stats = collection.num_entities
            return {
                "name": collection_name,
                "num_entities": stats,
                "description": collection.description
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {"error": str(e)}

    def health_check(self) -> bool:
        """
        Check if Milvus is healthy.

        Returns:
            True if Milvus is responsive
        """
        try:
            return utility.get_server_version() is not None
        except Exception:
            return False


# Global Milvus client instance
milvus_client = MilvusClient()
