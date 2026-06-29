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
            # 1. Embedding Cache Lookup
            from backend.cache.cache_keys import make_embedding_key
            from backend.cache.cache_service import cache_service, TTL_EMBEDDING, TTL_SEARCH
            
            embedding_key = make_embedding_key(query_text)
            query_vector = cache_service.get(embedding_key)
            if query_vector is None:
                query_vector = self.model.encode([query_text])[0].tolist()
                cache_service.set(embedding_key, query_vector, TTL_EMBEDDING)
                
            # 2. Qdrant Query Cache Lookup
            import hashlib
            import json
            vector_hash = hashlib.sha256(json.dumps(query_vector).encode("utf-8")).hexdigest()
            search_cache_key = f"qdrant_search:{collection_name}:{vector_hash}:{limit}"
            
            cached_search = cache_service.get(search_cache_key)
            if cached_search is not None:
                return cached_search
                
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
                
            cache_service.set(search_cache_key, retrieved, TTL_SEARCH)
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
