"""
Comprehensive test suite for the Text-to-CAD API
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the external dependencies before importing app
with patch("app.load_dotenv"):
    with patch("app.badcad"):
        with patch("app.genai"):
            from app import app, user_database, temp_models, collected_user_data

client = TestClient(app)


class TestAPIEndpoints:
    """Test all API endpoints"""

    def setup_method(self):
        """Reset state before each test"""
        user_database.clear()
        temp_models.clear()
        collected_user_data.clear()

    def test_generate_model_success(self):
        """Test successful model generation from prompt"""
        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                # Mock responses
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10, 10, 10)"
                )
                mock_execute.return_value = "/tmp/test_model.stl"

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
        user_id = "test_user_123"

        # Set up user with 10 models (limit)
        user_database[user_id] = {
            "email": "test@example.com",
            "name": "Test User",
            "model_count": 10,
        }

        response = client.post(
            "/api/generate", json={"prompt": "Create a cube", "user_id": user_id}
        )

        assert response.status_code == 403
        assert "limit reached" in response.json()["detail"]

    def test_generate_model_fallback_on_ai_failure(self):
        """Test fallback generation when AI fails"""
        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                # Mock AI failure
                mock_gemini.side_effect = Exception("AI service unavailable")
                mock_execute.return_value = "/tmp/test_model.stl"

                response = client.post(
                    "/api/generate", json={"prompt": "Create a sphere"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "fallback" in data["message"].lower()

    def test_execute_badcad_code_success(self):
        """Test direct BadCAD code execution"""
        with patch("app.execute_badcad_and_export") as mock_execute:
            mock_execute.return_value = "/tmp/test_model.stl"

            response = client.post(
                "/api/execute",
                json={"code": "from badcad import *\nmodel = sphere(r=5)"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "model_id" in data

    def test_execute_empty_code(self):
        """Test execute endpoint with empty code"""
        response = client.post(
            "/api/execute",
            json={
                "code": "   "  # Just whitespace
            },
        )

        assert response.status_code == 400
        assert "No code provided" in response.json()["detail"]

    def test_user_info_create_new_user(self):
        """Test creating a new user"""
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
        user_id = "existing_user_789"

        # Create initial user
        user_database[user_id] = {
            "email": "old@example.com",
            "name": "Old Name",
            "model_count": 5,
        }

        response = client.post(
            "/api/user/info",
            json={
                "user_id": user_id,
                "email": "updated@example.com",
                "name": "Updated Name",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_count"] == 5  # Should preserve count
        assert user_database[user_id]["email"] == "updated@example.com"

    def test_increment_user_count_success(self):
        """Test incrementing user model count"""
        user_id = "count_user_123"

        # Create user with some models
        user_database[user_id] = {
            "email": "count@example.com",
            "name": "Count User",
            "model_count": 3,
        }

        response = client.post("/api/user/increment-count", json={"user_id": user_id})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model_count"] == 4

    def test_increment_user_count_at_limit(self):
        """Test incrementing when at limit"""
        user_id = "limit_user_456"

        # Create user at limit
        user_database[user_id] = {
            "email": "limit@example.com",
            "name": "Limit User",
            "model_count": 10,
        }

        response = client.post("/api/user/increment-count", json={"user_id": user_id})

        assert response.status_code == 403
        assert "limit reached" in response.json()["detail"]

    def test_increment_nonexistent_user(self):
        """Test incrementing count for non-existent user"""
        response = client.post(
            "/api/user/increment-count", json={"user_id": "ghost_user"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_download_model_success(self):
        """Test downloading a generated model"""
        model_id = "download_test_123"

        # Create a temporary STL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as f:
            f.write("solid test\nendsolid test")
            temp_models[model_id] = f.name

        try:
            response = client.get(f"/api/download/{model_id}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            assert f"model_{model_id}.stl" in response.headers.get(
                "content-disposition", ""
            )
        finally:
            # Cleanup
            if os.path.exists(f.name):
                os.unlink(f.name)

    def test_download_nonexistent_model(self):
        """Test downloading non-existent model"""
        response = client.get("/api/download/fake_model_id")

        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]

    def test_admin_collected_emails_endpoint(self):
        """Test admin endpoint for viewing collected data"""
        # Add some test data
        with patch("app.load_collected_emails") as mock_load:
            mock_load.return_value = {
                "user1": {
                    "email": "user1@example.com",
                    "name": "User One",
                    "model_count": 3,
                    "prompts": [
                        {
                            "prompt": "Make a cube",
                            "type": "generate",
                            "timestamp": "2024-01-01T10:00:00",
                        },
                        {
                            "prompt": "Make a sphere",
                            "type": "generate",
                            "timestamp": "2024-01-01T11:00:00",
                        },
                    ],
                },
                "user2": {
                    "email": "user2@example.com",
                    "name": "User Two",
                    "model_count": 1,
                    "prompts": [],
                },
            }

            response = client.get("/api/admin/collected-emails")

            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 2
            assert data["total_prompts"] == 2
            assert data["total_models_generated"] == 4
            assert len(data["users"]) == 2


class TestHelperFunctions:
    """Test helper functions"""

    def test_generate_smart_fallback_for_cone(self):
        """Test smart fallback generates cone for cone-related prompts"""
        from app import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Create a cone shape")
        assert "cone" in code.lower() or "extrude_to" in code
        assert "model =" in code

    def test_generate_smart_fallback_for_sphere(self):
        """Test smart fallback generates sphere for sphere-related prompts"""
        from app import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Make a ball")
        assert "sphere" in code
        assert "model =" in code

    def test_generate_smart_fallback_for_cylinder(self):
        """Test smart fallback generates cylinder for cylinder-related prompts"""
        from app import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Create a tube")
        assert "cylinder" in code
        assert "model =" in code

    def test_generate_smart_fallback_default(self):
        """Test smart fallback default for unrecognized prompts"""
        from app import generate_smart_fallback_badcad_code

        code = generate_smart_fallback_badcad_code("Random object xyz")
        assert "box" in code.lower() or "square" in code
        assert "model =" in code

    def test_extract_badcad_code_from_markdown(self):
        """Test extracting code from markdown code blocks"""
        from app import extract_badcad_code

        response = """Here's the code:
```python
from badcad import *
model = cube(10, 10, 10)
```
That should work!"""

        code = extract_badcad_code(response)
        assert code == "from badcad import *\nmodel = cube(10, 10, 10)"

    def test_extract_badcad_code_without_blocks(self):
        """Test extracting code without markdown blocks"""
        from app import extract_badcad_code

        response = """from badcad import *
model = sphere(r=5)
This creates a sphere."""

        code = extract_badcad_code(response)
        assert "from badcad import *" in code
        assert "model = sphere(r=5)" in code

    def test_check_user_can_generate_new_user(self):
        """Test new users can generate"""
        from app import check_user_can_generate

        assert check_user_can_generate("brand_new_user") is True

    def test_check_user_can_generate_under_limit(self):
        """Test users under limit can generate"""
        from app import check_user_can_generate

        user_database["test_user"] = {"model_count": 5}
        assert check_user_can_generate("test_user") is True

    def test_check_user_can_generate_at_limit(self):
        """Test users at limit cannot generate"""
        from app import check_user_can_generate

        user_database["limit_user"] = {"model_count": 10}
        assert check_user_can_generate("limit_user") is False

    def test_create_fallback_stl(self):
        """Test fallback STL creation"""
        from app import create_fallback_stl

        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as f:
            test_path = f.name

        try:
            create_fallback_stl(test_path)

            # Verify file exists and has content
            assert os.path.exists(test_path)
            assert os.path.getsize(test_path) > 0

            # Verify it's a valid STL
            with open(test_path, "r") as f:
                content = f.read()
                assert content.startswith("solid cube")
                assert content.endswith("endsolid cube")
                assert "facet normal" in content
                assert "vertex" in content
        finally:
            if os.path.exists(test_path):
                os.unlink(test_path)


class TestDataPersistence:
    """Test data persistence functions"""

    def test_add_user_prompt_new_user(self):
        """Test adding prompt for new user"""
        from app import add_user_prompt

        with patch("app.load_collected_emails") as mock_load:
            with patch("app.save_collected_emails") as mock_save:
                mock_load.return_value = {}

                result = add_user_prompt(
                    "new_user", "new@example.com", "Make a cube", "generate"
                )

                assert result["email"] == "new@example.com"
                assert len(result["prompts"]) == 1
                assert result["prompts"][0]["prompt"] == "Make a cube"
                assert result["prompts"][0]["type"] == "generate"
                mock_save.assert_called_once()

    def test_add_user_prompt_existing_user(self):
        """Test adding prompt for existing user"""
        from app import add_user_prompt

        with patch("app.load_collected_emails") as mock_load:
            with patch("app.save_collected_emails") as mock_save:
                mock_load.return_value = {
                    "existing_user": {
                        "email": "existing@example.com",
                        "prompts": [{"prompt": "Old prompt", "type": "generate"}],
                        "model_count": 2,
                    }
                }

                result = add_user_prompt(
                    "existing_user",
                    "existing@example.com",
                    "New prompt",
                    "execute_code",
                )

                assert len(result["prompts"]) == 2
                assert result["prompts"][1]["prompt"] == "New prompt"
                assert result["prompts"][1]["type"] == "execute_code"
                mock_save.assert_called_once()


class TestGeminiIntegration:
    """Test Gemini AI integration"""

    def test_gemini_generation_success(self):
        """Test successful Gemini code generation"""
        from app import generate_badcad_code_with_gemini

        with patch("app.GEMINI_AVAILABLE", True):
            with patch("app.gemini_client") as mock_client:
                # Mock Gemini response
                mock_response = Mock()
                mock_response.text = """```python
from badcad import *
# Create a gear
gear = circle(r=10)
model = gear.extrude(5)
```"""
                mock_client.models.generate_content.return_value = mock_response

                code = generate_badcad_code_with_gemini("Create a gear")

                assert "from badcad import *" in code
                assert "model =" in code
                assert "gear" in code

    def test_gemini_quota_exhausted(self):
        """Test handling of quota exhaustion"""
        from app import generate_badcad_code_with_gemini

        with patch("app.GEMINI_AVAILABLE", True):
            with patch("app.gemini_client") as mock_client:
                mock_client.models.generate_content.side_effect = Exception(
                    "RESOURCE_EXHAUSTED: Quota exceeded"
                )

                code = generate_badcad_code_with_gemini("Create something")

                # Should return fallback code
                assert "from badcad import *" in code
                assert "model =" in code

    def test_gemini_permission_denied(self):
        """Test handling of permission errors"""
        from app import generate_badcad_code_with_gemini

        with patch("app.GEMINI_AVAILABLE", True):
            with patch("app.gemini_client") as mock_client:
                mock_client.models.generate_content.side_effect = Exception(
                    "PERMISSION_DENIED"
                )

                code = generate_badcad_code_with_gemini("Create a box")

                # Should return fallback code
                assert "from badcad import *" in code
                assert "model =" in code


class TestBadCADExecution:
    """Test BadCAD code execution"""

    def test_execute_badcad_success(self):
        """Test successful BadCAD execution"""
        from app import execute_badcad_and_export

        with patch("app.BADCAD_AVAILABLE", True):
            # Create a mock model with stl() method
            mock_model = Mock()
            mock_model.stl.return_value = b"solid test\nendsolid test"

            with patch("builtins.exec") as mock_exec:
                # Make exec populate 'model' in globals
                def exec_side_effect(code, globals_dict):
                    globals_dict["model"] = mock_model

                mock_exec.side_effect = exec_side_effect

                stl_path = execute_badcad_and_export(
                    "from badcad import *\nmodel = cube(10,10,10)", "test_123"
                )

                assert os.path.exists(stl_path)
                assert "test_123" in stl_path

                # Cleanup
                if os.path.exists(stl_path):
                    os.unlink(stl_path)

    def test_execute_badcad_no_model_variable(self):
        """Test handling when no 'model' variable is created"""
        from app import execute_badcad_and_export

        with patch("app.BADCAD_AVAILABLE", True):
            with patch("builtins.exec"):
                # Don't populate 'model' variable
                stl_path = execute_badcad_and_export("x = 5", "test_456")

                # Should create fallback STL
                assert os.path.exists(stl_path)

                with open(stl_path, "r") as f:
                    content = f.read()
                    assert "solid cube" in content

                # Cleanup
                if os.path.exists(stl_path):
                    os.unlink(stl_path)

    def test_execute_badcad_not_available(self):
        """Test execution when BadCAD is not available"""
        from app import execute_badcad_and_export

        with patch("app.BADCAD_AVAILABLE", False):
            stl_path = execute_badcad_and_export("from badcad import *", "test_789")

            # Should create fallback STL
            assert os.path.exists(stl_path)

            with open(stl_path, "r") as f:
                content = f.read()
                assert "solid cube" in content

            # Cleanup
            if os.path.exists(stl_path):
                os.unlink(stl_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
