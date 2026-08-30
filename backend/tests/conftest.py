import os
import pytest

# Force tests to use a local SQLite test database instead of production Postgres
# This prevents tests from corrupting production data and fixes the tests that rely on an empty state
os.environ["DATABASE_URL"] = "sqlite:///./data/test.db"

# Now we can safely import the backend modules
from backend.app.repositories.database import init_db, get_db_connection

@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure a clean database before each test."""
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)
    
    # Remove old test DB if it exists
    if os.path.exists("./data/test.db"):
        os.remove("./data/test.db")
        
    # Initialize fresh DB
    init_db()
    yield
    # Teardown after test
    if os.path.exists("./data/test.db"):
        os.remove("./data/test.db")
