import sys
from pathlib import Path
from sqlalchemy import text

# Enable absolute path imports for the backend directory
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.session import SessionLocal, engine

def test_database_connection():
    """Verifies that we can connect to the PostgreSQL instance and execute basic SQL."""
    db = SessionLocal()
    try:
        # Check standard ping
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1, "Database ping failed to return 1"
        print("✔ Database connection and query execution succeeded.")
    except Exception as e:
        assert False, f"PostgreSQL database connection failed: {e}"
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connection()
