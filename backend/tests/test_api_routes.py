"""
Tests for API routes

Comprehensive test suite for all API endpoints to ensure they work correctly
with the new modular service architecture.
"""
import pytest
import json
import uuid
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routes.generation import router as generation_router
from api.routes.download import router as download_router
from api.routes.user import router as user_router
from api.routes.admin import router as admin_router


@pytest.fixture
def test_app():
    """Create a test FastAPI app with all routes"""
    app = FastAPI()
    app.include_router(generation_router)
    app.include_router(download_router)
    app.include_router(user_router)
    app.include_router(admin_router)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app)


@pytest.fixture
def mock_services():
    """Mock all services for testing"""
    with patch('api.routes.generation.ai_generator') as mock_ai, \
         patch('api.routes.generation.badcad_executor') as mock_executor, \
         patch('api.routes.generation.user_manager') as mock_user, \
         patch('api.routes.generation.model_storage') as mock_storage, \
         patch('api.routes.download.model_storage') as mock_dl_storage, \
         patch('api.routes.user.user_manager') as mock_user_mgr, \
         patch('api.routes.admin.user_manager') as mock_admin_user:
        
        # Configure mocks
        mock_ai.generate_badcad_code.return_value = "from badcad import *\nmodel = cube(10, 10, 10)"
        mock_executor.execute_and_export.return_value = "/tmp/test.stl"
        mock_user.check_user_can_generate.return_value = True
        mock_user.record_user_prompt.return_value = None
        mock_user.increment_user_model_count.return_value = 1
        mock_storage.store_model.return_value = None
        
        yield {
            'ai_generator': mock_ai,
            'badcad_executor': mock_executor,
            'user_manager': mock_user,
            'model_storage': mock_storage,
            'dl_storage': mock_dl_storage,
            'user_mgr': mock_user_mgr,
            'admin_user': mock_admin_user
        }


class TestGenerationRoutes:
    """Test generation API endpoints"""
    
    def test_generate_model_success(self, client, mock_services):
        """Test successful model generation"""
        response = client.post("/api/generate", json={
            "prompt": "Create a simple cube",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "model_id" in data
        assert data["badcad_code"] == "from badcad import *\nmodel = cube(10, 10, 10)"
        assert "Generated model for" in data["message"]
    
    def test_generate_model_no_prompt(self, client, mock_services):
        """Test generation with empty prompt"""
        response = client.post("/api/generate", json={
            "prompt": "   ",  # Whitespace only to test strip()
            "user_id": "test_user"
        })
        
        assert response.status_code == 400
        assert "No prompt provided" in response.json()["detail"]
    
    def test_generate_model_user_limit_exceeded(self, client, mock_services):
        """Test generation when user limit is exceeded"""
        mock_services['user_manager'].check_user_can_generate.return_value = False
        
        response = client.post("/api/generate", json={
            "prompt": "Create a cube",
            "user_id": "test_user"
        })
        
        assert response.status_code == 403
        assert "limit reached" in response.json()["detail"]
    
    def test_execute_badcad_code_success(self, client, mock_services):
        """Test successful BadCAD code execution"""
        response = client.post("/api/execute", json={
            "code": "from badcad import *\nmodel = cube(5, 5, 5)",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "model_id" in data
        assert "executed successfully" in data["message"]
    
    def test_execute_badcad_code_empty(self, client, mock_services):
        """Test execution with empty code"""
        response = client.post("/api/execute", json={
            "code": "   ",  # Whitespace only to test strip()
            "user_id": "test_user"
        })
        
        assert response.status_code == 400
        assert "No code provided" in response.json()["detail"]


class TestDownloadRoutes:
    """Test download API endpoints"""
    
    def test_download_model_success(self, client, mock_services):
        """Test successful model download"""
        model_id = str(uuid.uuid4())
        
        # Create a temporary STL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
            f.write("solid test\nendsolid test")
            temp_path = f.name
        
        mock_services['dl_storage'].get_model_path.return_value = temp_path
        
        try:
            response = client.get(f"/api/download/{model_id}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
        finally:
            os.unlink(temp_path)
    
    def test_download_model_not_found(self, client, mock_services):
        """Test download of non-existent model"""
        mock_services['dl_storage'].get_model_path.return_value = None
        
        response = client.get("/api/download/nonexistent")
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]
    
    def test_download_model_invalid_id(self, client, mock_services):
        """Test download with invalid model ID"""
        response = client.get("/api/download/short")
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]


class TestUserRoutes:
    """Test user management API endpoints"""
    
    def test_get_user_info_new_user(self, client, mock_services):
        """Test creating new user info"""
        mock_services['user_mgr'].create_or_update_user.return_value = {
            'model_count': 0
        }
        mock_services['user_mgr'].max_models_per_user = 10
        
        response = client.post("/api/user/info", json={
            "user_id": "new_user",
            "email": "test@example.com",
            "name": "Test User"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "new_user"
        assert data["model_count"] == 0
        assert data["max_models"] == 10
    
    def test_get_user_info_missing_fields(self, client, mock_services):
        """Test user info with missing required fields"""
        response = client.post("/api/user/info", json={
            "user_id": "",
            "email": "test@example.com",
            "name": "Test User"
        })
        
        assert response.status_code == 400
        assert "Missing required user information" in response.json()["detail"]
    
    def test_increment_user_count_success(self, client, mock_services):
        """Test successful user count increment"""
        mock_services['user_mgr'].increment_user_model_count.return_value = 3
        
        response = client.post("/api/user/increment-count", json={
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model_count"] == 3
    
    def test_increment_user_count_missing_user(self, client, mock_services):
        """Test increment count with missing user ID"""
        response = client.post("/api/user/increment-count", json={
            "user_id": ""
        })
        
        assert response.status_code == 400
        assert "User ID is required" in response.json()["detail"]


class TestAdminRoutes:
    """Test admin API endpoints"""
    
    def test_get_collected_emails_success(self, client, mock_services):
        """Test successful admin data retrieval"""
        mock_services['admin_user'].get_all_users_summary.return_value = {
            'total_users': 2,
            'total_prompts': 5,
            'total_models_generated': 3,
            'users': [
                {
                    'user_id': 'user1',
                    'email': 'user1@example.com',
                    'name': 'User One',
                    'model_count': 2,
                    'total_prompts': 3,
                    'created_at': '2024-01-01T00:00:00',
                    'last_activity': '2024-01-02T00:00:00',
                    'recent_prompts': []
                }
            ]
        }
        
        response = client.get("/api/admin/collected-emails")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 2
        assert data["total_prompts"] == 5
        assert data["total_models_generated"] == 3
        assert len(data["users"]) == 1
    
    def test_delete_user_success(self, client, mock_services):
        """Test successful user deletion"""
        mock_services['admin_user'].delete_user.return_value = True
        
        response = client.delete("/api/admin/user/test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"]
    
    def test_delete_user_not_found(self, client, mock_services):
        """Test deletion of non-existent user"""
        mock_services['admin_user'].delete_user.return_value = False
        
        response = client.delete("/api/admin/user/nonexistent")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_reset_user_count_success(self, client, mock_services):
        """Test successful user count reset"""
        mock_services['admin_user'].get_user.return_value = {'model_count': 5}
        mock_services['admin_user'].reset_user_count.return_value = None
        
        response = client.post("/api/admin/user/test_user/reset-count")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset to 0" in data["message"]
    
    def test_reset_user_count_user_not_found(self, client, mock_services):
        """Test count reset for non-existent user"""
        mock_services['admin_user'].get_user.return_value = None
        
        response = client.post("/api/admin/user/nonexistent/reset-count")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


@pytest.mark.integration
class TestIntegrationRoutes:
    """Integration tests with real services (optional)"""
    
    def test_full_generation_flow(self, client):
        """Test complete generation flow without mocks"""
        # This would test with real services if needed
        # Skipped for now to avoid dependencies
        pytest.skip("Integration test - requires real services")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])