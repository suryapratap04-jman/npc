import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings

def test_embeddings_generation():
    """Verifies that the configured SentenceTransformer model loads and generates embeddings."""
    try:
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        test_txt = "Senior Software Engineer with Python and SQL experience."
        embedding = model.encode([test_txt])[0]
        
        # Output should be list of floats
        assert len(embedding) > 0, "Embedding generation returned empty vector."
        assert isinstance(embedding[0], float) or type(embedding[0]).__name__ == 'float32', "Embedding elements must be floats."
        print(f"✔ Local embeddings generation succeeded. Vector dimension: {len(embedding)}")
    except Exception as e:
        assert False, f"Embedding generation pipeline test failed: {e}"

if __name__ == "__main__":
    test_embeddings_generation()
