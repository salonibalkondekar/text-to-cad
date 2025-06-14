"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ["GEMINI_API_KEY"] = "test_api_key"
os.environ["TESTING"] = "true"


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup any test files created during tests"""
    yield
    
    # Remove any test JSON files
    test_json = backend_dir / "collected_user_emails.json"
    if test_json.exists():
        test_json.unlink()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_12345")
    monkeypatch.setenv("BADCAD_AVAILABLE", "true")
    yield


@pytest.fixture
def temp_stl_file(tmp_path):
    """Create a temporary STL file for testing"""
    stl_content = """solid test_model
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.0 1.0 0.0
    endloop
  endfacet
endsolid test_model"""
    
    stl_file = tmp_path / "test_model.stl"
    stl_file.write_text(stl_content)
    return str(stl_file)