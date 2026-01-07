"""
Milvus initialization script.

This script creates required Milvus collections for the application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog

from src.utils.milvus_client import milvus_client
from src.core.config import settings

logger = structlog.get_logger(__name__)


def init_milvus():
    """Initialize Milvus collections."""
    try:
        logger.info("Initializing Milvus...")
        logger.info(f"Milvus host: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        
        # The MilvusClient already creates collections on initialization
        # We just need to verify they exist
        
        collections = ["translations", "document_chunks", "summaries"]
        
        for collection_name in collections:
            try:
                stats = milvus_client.get_collection_stats(collection_name)
                logger.info(f"Collection '{collection_name}' initialized: {stats.get('num_entities', 0)} entities")
            except Exception as e:
                logger.error(f"Failed to get stats for collection '{collection_name}': {e}")
        
        # Test health
        if milvus_client.health_check():
            logger.info("Milvus health check: OK")
        else:
            logger.warning("Milvus health check: FAILED")
        
        logger.info("Milvus initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Milvus initialization failed: {e}")
        logger.error("Make sure Milvus is running and accessible")
        return False


if __name__ == "__main__":
    success = init_milvus()
    sys.exit(0 if success else 1)
