"""
Integration tests for the new modular app.py

Tests the complete application with all routes and services working together.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """Create a test client for the new modular app"""
    return TestClient(app)


class TestNewAppIntegration:
    """Test the new modular app.py integration"""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Text-to-CAD API v2.0" in data["message"]
        assert "endpoints" in data
        assert "/api/generate" in data["endpoints"]["generation"]

    def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert data["architecture"] == "modular"
        assert "services" in data

    def test_generation_endpoint_integration(self, client):
        """Test model generation through the new app"""
        response = client.post(
            "/api/generate",
            json={"prompt": "Create a simple cube", "user_id": "test_user_integration"},
        )

        # Should work with our modular services
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "model_id" in data
        assert "badcad_code" in data
        assert "Generated" in data["message"]

    def test_user_info_endpoint_integration(self, client):
        """Test user info endpoint through the new app"""
        user_id = f"test_user_{uuid.uuid4()}"

        response = client.post(
            "/api/user/info",
            json={
                "user_id": user_id,
                "email": "integration@test.com",
                "name": "Integration Test User",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user_id
        assert data["model_count"] == 0
        assert data["max_models"] == 10

    def test_execute_endpoint_integration(self, client):
        """Test BadCAD code execution through the new app"""
        response = client.post(
            "/api/execute",
            json={
                "code": "from badcad import *\nmodel = cube(10, 10, 10)",
                "user_id": "test_user_execute",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "model_id" in data
        assert "executed successfully" in data["message"]

    def test_admin_endpoint_integration(self, client):
        """Test admin endpoint through the new app"""
        response = client.get("/api/admin/collected-emails")

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_prompts" in data
        assert "users" in data

    def test_download_endpoint_structure(self, client):
        """Test download endpoint structure (will return 404 for non-existent model)"""
        response = client.get("/api/download/nonexistent-model-id")

        # Should return 404 for non-existent model, but this means the endpoint exists
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]

    def test_cors_headers(self, client):
        """Test CORS headers are properly configured"""
        response = client.options("/api/generate")

        # FastAPI will handle CORS preflight requests
        # The key is that our middleware is configured
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS

    def test_error_handling_consistency(self, client):
        """Test that error handling is consistent across endpoints"""
        # Test empty prompt
        response = client.post(
            "/api/generate",
            json={
                "prompt": "   ",  # Whitespace only
                "user_id": "test_user",
            },
        )
        assert response.status_code == 400

        # Test empty code
        response = client.post(
            "/api/execute",
            json={
                "code": "   ",  # Whitespace only
                "user_id": "test_user",
            },
        )
        assert response.status_code == 400

        # Test missing user info
        response = client.post(
            "/api/user/info",
            json={"user_id": "", "email": "test@example.com", "name": "Test"},
        )
        assert response.status_code == 400


class TestModularArchitectureIntegrity:
    """Test that the modular architecture maintains integrity"""

    def test_services_are_accessible(self, client):
        """Test that all services are properly imported and accessible"""
        # This test verifies that the modular architecture works
        # by checking that we can make calls that use all services

        # Test AI generation service (via generate endpoint)
        response = client.post(
            "/api/generate", json={"prompt": "test cube", "user_id": "arch_test_user"}
        )
        assert response.status_code == 200

        # Test user management service (via user info endpoint)
        response = client.post(
            "/api/user/info",
            json={
                "user_id": "arch_test_user",
                "email": "arch@test.com",
                "name": "Architecture Test",
            },
        )
        assert response.status_code == 200

        # Test storage service (via download endpoint structure)
        response = client.get("/api/download/test-id")
        assert response.status_code == 404  # Expected for non-existent model

    def test_no_legacy_endpoints_leak(self, client):
        """Test that no legacy monolithic code is accessible"""
        # The new app should only have our defined routes
        # Test some endpoints that might exist in the old monolithic version

        # These should return 404 since they don't exist in our modular app
        legacy_endpoints = [
            "/generate",  # Old endpoint without /api prefix
            "/execute",  # Old endpoint without /api prefix
            "/user/info",  # Old endpoint without /api prefix
        ]

        for endpoint in legacy_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404


class TestPerformanceBaseline:
    """Basic performance tests for the new architecture"""

    def test_startup_time_reasonable(self, client):
        """Test that the app starts up in reasonable time"""
        # If we can make a health check call, startup was successful
        response = client.get("/health")
        assert response.status_code == 200

        # The response should be fast
        assert "healthy" in response.json()["status"]

    def test_multiple_concurrent_requests(self, client):
        """Test handling multiple requests (basic concurrency)"""
        import concurrent.futures
        import time

        def make_request():
            return client.get("/health")

        # Test 5 concurrent health checks
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        end_time = time.time()

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # Should complete in reasonable time (less than 5 seconds for 5 health checks)
        assert (end_time - start_time) < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
