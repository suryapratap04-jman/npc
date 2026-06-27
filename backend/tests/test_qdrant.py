import sys
from pathlib import Path
from qdrant_client import QdrantClient

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings

def test_qdrant_connection():
    """Verifies connection to the Qdrant Vector database and checks collections status."""
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        collections = client.get_collections()
        assert collections is not None, "Failed to retrieve collections list from Qdrant."
        print(f"✔ Qdrant connection succeeded. Active collections: {collections.collections}")
    except Exception as e:
        assert False, f"Qdrant vector database connection failed: {e}"

if __name__ == "__main__":
    test_qdrant_connection()
