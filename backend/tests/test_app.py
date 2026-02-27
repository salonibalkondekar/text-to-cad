"""
Comprehensive test suite for the Text-to-CAD API

Tests API endpoints, helper functions, and service integrations
for the modular FastAPI application.
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test all API endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "services" in data

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Text-to-CAD" in data["message"]
        assert "docs" in data
        assert "endpoints" in data

    def test_generate_model_success(self):
        """Test successful model generation from prompt"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10, 10, 10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/test_model.stl"

            response = client.post(
                "/api/generate", json={"prompt": "Create a simple cube"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "model_id" in data
            assert "badcad_code" in data
            assert "cube" in data["badcad_code"]

    def test_generate_model_with_user_limit(self):
        """Test model generation respects user limits"""
        with patch("api.routes.generation.user_manager") as mock_um:
            from core.exceptions import UserLimitExceededError

            mock_um.check_user_limit = AsyncMock(
                side_effect=UserLimitExceededError("test_user", 10, 10)
            )

            response = client.post(
                "/api/generate",
                json={"prompt": "Create a cube", "user_id": "test_user_123"},
            )

            assert response.status_code == 403
            assert "limit reached" in response.json()["detail"].lower()

    def test_generate_model_fallback_on_ai_failure(self):
        """Test fallback generation when AI fails"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            from core.exceptions import AIGenerationError

            mock_ai.generate_badcad_code.side_effect = AIGenerationError(
                "AI service unavailable"
            )
            mock_ai._generate_fallback_code.return_value = (
                "from badcad import *\nmodel = cube(10, 10, 10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/fallback.stl"

            response = client.post("/api/generate", json={"prompt": "Create a sphere"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "fallback" in data["message"].lower()

    def test_execute_badcad_code_success(self):
        """Test direct BadCAD code execution"""
        with (
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_exec.execute_and_export.return_value = "/tmp/test_model.stl"

            response = client.post(
                "/api/execute",
                json={"code": "from badcad import *\nmodel = sphere(r=5)"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "model_id" in data

    def test_execute_empty_code(self):
        """Test execute endpoint with empty/whitespace code"""
        response = client.post(
            "/api/execute",
            json={"code": "   "},
        )

        assert response.status_code == 400
        assert "No code provided" in response.json()["detail"]

    def test_user_info_create_new_user(self):
        """Test creating a new user"""
        with patch("api.routes.user.analytics_client") as mock_analytics:
            mock_analytics.create_session = AsyncMock(
                return_value={
                    "user": {"model_count": 0},
                    "session_id": "test_session",
                    "csrf_token": "test_csrf",
                }
            )

            response = client.post(
                "/api/user/info",
                json={
                    "user_id": "new_user_456",
                    "email": "newuser@example.com",
                    "name": "New User",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user_id"] == "new_user_456"
            assert data["model_count"] == 0
            assert data["max_models"] == 10

    def test_user_info_update_existing_user(self):
        """Test updating existing user info"""
        with patch("api.routes.user.analytics_client") as mock_analytics:
            mock_analytics.create_session = AsyncMock(
                return_value={
                    "user": {"model_count": 5},
                    "session_id": "test_session",
                    "csrf_token": "test_csrf",
                }
            )

            response = client.post(
                "/api/user/info",
                json={
                    "user_id": "existing_user_789",
                    "email": "updated@example.com",
                    "name": "Updated Name",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model_count"] == 5

    def test_download_model_success(self):
        """Test downloading a generated model"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as f:
            f.write("solid test\nendsolid test")
            stl_path = f.name

        # Use UUID-length model_id (download route checks len >= 10)
        model_id = "a" * 36

        try:
            with (
                patch("api.routes.download.model_storage") as mock_storage,
                patch("api.routes.download.user_manager") as mock_um,
            ):
                mock_storage.get_model_path.return_value = stl_path
                mock_um.track_model_download = AsyncMock()

                response = client.get(f"/api/download/{model_id}")

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/octet-stream"
                assert f"model_{model_id}.stl" in response.headers.get(
                    "content-disposition", ""
                )
        finally:
            if os.path.exists(stl_path):
                os.unlink(stl_path)

    def test_download_nonexistent_model(self):
        """Test downloading non-existent model"""
        model_id = "a" * 36

        with patch("api.routes.download.model_storage") as mock_storage:
            mock_storage.get_model_path.return_value = None

            response = client.get(f"/api/download/{model_id}")

            assert response.status_code == 404
            assert "Model not found" in response.json()["detail"]

    def test_admin_collected_emails_endpoint(self):
        """Test admin endpoint for viewing collected data"""
        with patch("api.routes.admin.user_manager") as mock_um:
            mock_um.get_all_users_summary.return_value = {
                "total_users": 2,
                "total_prompts": 2,
                "total_models_generated": 4,
                "users": [
                    {
                        "user_id": "user1",
                        "email": "user1@example.com",
                        "name": "User One",
                        "model_count": 3,
                        "total_prompts": 2,
                        "created_at": "2024-01-01T10:00:00",
                        "last_activity": "2024-01-01T11:00:00",
                        "recent_prompts": [],
                    },
                    {
                        "user_id": "user2",
                        "email": "user2@example.com",
                        "name": "User Two",
                        "model_count": 1,
                        "total_prompts": 0,
                        "created_at": "2024-01-01T10:00:00",
                        "last_activity": "2024-01-01T11:00:00",
                        "recent_prompts": [],
                    },
                ],
            }

            response = client.get("/api/admin/collected-emails")

            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 2
            assert data["total_prompts"] == 2
            assert data["total_models_generated"] == 4
            assert len(data["users"]) == 2


class TestHelperFunctions:
    """Test utility helper functions from their new modular locations"""

    def test_generate_smart_fallback_for_cone(self):
        """Test smart fallback generates cone for cone-related prompts"""
        from utils.stl_fallback import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Create a cone shape")
        assert "cone" in code.lower() or "extrude_to" in code
        assert "model =" in code

    def test_generate_smart_fallback_for_sphere(self):
        """Test smart fallback generates sphere for sphere-related prompts"""
        from utils.stl_fallback import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Make a ball")
        assert "sphere" in code
        assert "model =" in code

    def test_generate_smart_fallback_for_cylinder(self):
        """Test smart fallback generates cylinder for cylinder-related prompts"""
        from utils.stl_fallback import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Create a tube")
        assert "cylinder" in code
        assert "model =" in code

    def test_generate_smart_fallback_default(self):
        """Test smart fallback default for unrecognized prompts"""
        from utils.stl_fallback import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Random object xyz")
        assert "box" in code.lower() or "square" in code
        assert "model =" in code

    def test_extract_badcad_code_from_markdown(self):
        """Test extracting code from markdown code blocks"""
        from utils.code_extraction import extract_badcad_code

        response_text = """Here's the code:
```python
from badcad import *
model = cube(10, 10, 10)
```
That should work!"""

        code = extract_badcad_code(response_text)
        assert code == "from badcad import *\nmodel = cube(10, 10, 10)"

    def test_extract_badcad_code_without_blocks(self):
        """Test extracting code without markdown blocks"""
        from utils.code_extraction import extract_badcad_code

        response_text = """from badcad import *
model = sphere(r=5)
This creates a sphere."""

        code = extract_badcad_code(response_text)
        assert "from badcad import *" in code
        assert "model = sphere(r=5)" in code

    def test_create_fallback_stl(self):
        """Test fallback STL creation"""
        from utils.stl_fallback import create_fallback_stl

        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as f:
            test_path = f.name

        try:
            create_fallback_stl(test_path)

            assert os.path.exists(test_path)
            assert os.path.getsize(test_path) > 0

            with open(test_path, "r") as f:
                content = f.read()
                assert content.startswith("solid cube")
                assert content.endswith("endsolid cube")
                assert "facet normal" in content
                assert "vertex" in content
        finally:
            if os.path.exists(test_path):
                os.unlink(test_path)


class TestGeminiIntegration:
    """Test Gemini AI integration through the API"""

    def test_generate_with_ai_success(self):
        """Test successful AI code generation through the API"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\n"
                "gear = circle(r=10)\n"
                "model = gear.extrude(5)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/gear.stl"

            response = client.post("/api/generate", json={"prompt": "Create a gear"})

            assert response.status_code == 200
            data = response.json()
            assert "from badcad import *" in data["badcad_code"]
            assert "model =" in data["badcad_code"]

    def test_generate_ai_quota_exhausted(self):
        """Test handling of AI quota exhaustion"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            from core.exceptions import AIGenerationError

            mock_ai.generate_badcad_code.side_effect = AIGenerationError(
                "RESOURCE_EXHAUSTED: Quota exceeded"
            )
            mock_ai._generate_fallback_code.return_value = (
                "from badcad import *\nmodel = cube(10, 10, 10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/fallback.stl"

            response = client.post("/api/generate", json={"prompt": "Create something"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "fallback" in data["message"].lower()
            assert "from badcad import *" in data["badcad_code"]

    def test_generate_ai_permission_denied(self):
        """Test handling of AI permission errors"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            from core.exceptions import AIGenerationError

            mock_ai.generate_badcad_code.side_effect = AIGenerationError(
                "PERMISSION_DENIED"
            )
            mock_ai._generate_fallback_code.return_value = (
                "from badcad import *\nmodel = cube(10, 10, 10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/fallback.stl"

            response = client.post("/api/generate", json={"prompt": "Create a box"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "from badcad import *" in data["badcad_code"]


class TestBadCADExecution:
    """Test BadCAD code execution through the API"""

    def test_execute_success(self):
        """Test successful BadCAD execution"""
        with (
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_exec.execute_and_export.return_value = "/tmp/test.stl"

            response = client.post(
                "/api/execute",
                json={"code": "from badcad import *\nmodel = cube(10,10,10)"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_exec.execute_and_export.assert_called_once()

    def test_execute_failure(self):
        """Test BadCAD execution failure"""
        with patch("api.routes.generation.badcad_executor") as mock_exec:
            from core.exceptions import BadCADExecutionError

            mock_exec.execute_and_export.side_effect = BadCADExecutionError(
                "Execution failed"
            )

            response = client.post(
                "/api/execute",
                json={"code": "from badcad import *\nmodel = invalid()"},
            )

            assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
