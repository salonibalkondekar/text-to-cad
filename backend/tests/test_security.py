"""
Security and edge case tests for the Text-to-CAD API
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


class TestSecurityConcerns:
    """Test security-related issues"""

    def test_path_traversal_in_download(self):
        """Test path traversal attempts in download endpoint"""
        dangerous_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for dangerous_id in dangerous_ids:
            response = client.get(f"/api/download/{dangerous_id}")
            # Should return 404, not expose system files
            assert response.status_code == 404

    def test_sql_injection_in_user_id(self):
        """Test SQL injection attempts in user_id field"""
        with patch("api.routes.user.analytics_client") as mock_analytics:
            mock_analytics.create_session = AsyncMock(
                return_value={
                    "user": {"model_count": 0},
                    "session_id": "test",
                    "csrf_token": "test",
                }
            )

            response = client.post(
                "/api/user/info",
                json={
                    "user_id": "'; DROP TABLE users; --",
                    "email": "hacker@evil.com",
                    "name": "Bobby Tables",
                },
            )

            # Should handle gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_xss_in_prompt(self):
        """Test XSS attempts in prompt field"""
        xss_prompt = "<script>alert('XSS')</script>Create a cube"

        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/safe.stl"

            response = client.post("/api/generate", json={"prompt": xss_prompt})

            assert response.status_code == 200
            # XSS should be passed to AI but not executed
            mock_ai.generate_badcad_code.assert_called_with(xss_prompt)

    def test_admin_endpoint_no_auth(self):
        """Test that admin endpoint is accessible without auth"""
        with patch("api.routes.admin.user_manager") as mock_um:
            mock_um.get_all_users_summary.return_value = {
                "total_users": 0,
                "total_prompts": 0,
                "total_models_generated": 0,
                "users": [],
            }

            response = client.get("/api/admin/collected-emails")

            # Currently returns 200 - this documents the security issue
            assert response.status_code == 200

    def test_cors_all_origins(self):
        """Test CORS configuration allows all origins"""
        response = client.options(
            "/api/generate",
            headers={
                "Origin": "http://evil-site.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Currently allows all origins - documents the security issue
        assert response.status_code == 200


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_prompt(self):
        """Test empty prompt handling"""
        response = client.post("/api/generate", json={"prompt": ""})
        # Pydantic min_length=1 validation rejects empty string
        assert response.status_code == 422

    def test_whitespace_only_prompt(self):
        """Test whitespace-only prompt handling"""
        response = client.post("/api/generate", json={"prompt": "   "})
        assert response.status_code == 400
        assert "No prompt provided" in response.json()["detail"]

    def test_very_long_prompt(self):
        """Test handling of very long prompts"""
        long_prompt = "Create a cube " * 1000

        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/test.stl"

            response = client.post("/api/generate", json={"prompt": long_prompt})

            assert response.status_code == 200

    def test_unicode_in_prompt(self):
        """Test Unicode characters in prompt"""
        unicode_prompt = "创建一个立方体 with émojis and ñ characters"

        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/test.stl"

            response = client.post("/api/generate", json={"prompt": unicode_prompt})

            assert response.status_code == 200

    def test_special_characters_in_email(self):
        """Test special characters in email addresses"""
        valid_emails = [
            "user.name@sub.domain.com",
            "user_123@example-site.com",
        ]

        for email in valid_emails:
            with patch("api.routes.user.analytics_client") as mock_analytics:
                mock_analytics.create_session = AsyncMock(
                    return_value={
                        "user": {"model_count": 0},
                        "session_id": "test",
                        "csrf_token": "test",
                    }
                )

                response = client.post(
                    "/api/user/info",
                    json={
                        "user_id": f"user_{email.replace('@', '_at_')}",
                        "email": email,
                        "name": "Special User",
                    },
                )

                assert response.status_code == 200


class TestDataValidation:
    """Test input validation and sanitization"""

    def test_invalid_json_format(self):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/generate",
            content="{'invalid': json syntax}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self):
        """Test missing required fields"""
        # Missing prompt
        response = client.post("/api/generate", json={})
        assert response.status_code == 422

        # Missing code
        response = client.post("/api/execute", json={})
        assert response.status_code == 422

        # Missing user_id in increment
        response = client.post("/api/user/increment-count", json={})
        assert response.status_code == 422

    def test_additional_unexpected_fields(self):
        """Test handling of unexpected extra fields"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/test.stl"

            response = client.post(
                "/api/generate",
                json={
                    "prompt": "Create a cube",
                    "unexpected_field": "should be ignored",
                    "another_field": 123,
                },
            )

            # Should work, ignoring extra fields
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
