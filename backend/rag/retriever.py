import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class VectorRetriever:
    """Retrieves context-rich records from Qdrant vector database."""
    
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        logger.info(f"Loading local embedding model for retrieval: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
    def _search_collection(self, collection_name: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            # Generate query vector
            query_vector = self.model.encode([query_text])[0].tolist()
            
            # Query Qdrant
            res = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit
            )
            
            retrieved = []
            for item in res.points:
                retrieved.append({
                    "id": item.id,
                    "score": item.score,
                    "payload": item.payload
                })
            return retrieved
        except Exception as e:
            logger.error(f"Vector search failed on collection '{collection_name}': {e}")
            return []
            
    def retrieve_employees(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving matching employees for: '{query_text}'")
        return self._search_collection("employees", query_text, limit)
        
    def retrieve_projects(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving matching projects for: '{query_text}'")
        return self._search_collection("projects", query_text, limit)

    def retrieve_pipeline(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving matching pipeline opportunities for: '{query_text}'")
        return self._search_collection("pipeline", query_text, limit)
