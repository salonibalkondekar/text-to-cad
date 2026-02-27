"""
Integration tests for the Text-to-CAD API
Tests complete workflows and interactions between components
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to model generation"""

    def test_new_user_generate_and_download_workflow(self):
        """Test complete workflow: register user, generate model, download"""
        # Step 1: Register new user
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
                    "user_id": "workflow_user",
                    "email": "workflow@example.com",
                    "name": "Workflow User",
                },
            )
            assert response.status_code == 200
            assert response.json()["model_count"] == 0

        # Step 2: Generate a model
        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as f:
            f.write("solid test\nendsolid test")
            stl_path = f.name

        try:
            with (
                patch("api.routes.generation.ai_generator") as mock_ai,
                patch("api.routes.generation.badcad_executor") as mock_exec,
                patch("api.routes.generation.model_storage"),
            ):
                mock_ai.generate_badcad_code.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_exec.execute_and_export.return_value = stl_path

                response = client.post(
                    "/api/generate",
                    json={"prompt": "Create a cube"},
                )
                assert response.status_code == 200
                model_data = response.json()
                model_id = model_data["model_id"]
                assert model_data["success"] is True

            # Step 3: Download the model
            with (
                patch("api.routes.download.model_storage") as mock_storage,
                patch("api.routes.download.user_manager") as mock_um,
            ):
                mock_storage.get_model_path.return_value = stl_path
                mock_um.track_model_download = AsyncMock()

                response = client.get(f"/api/download/{model_id}")
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/octet-stream"
        finally:
            if os.path.exists(stl_path):
                os.unlink(stl_path)

    def test_generate_then_execute_workflow(self):
        """Test generating with AI then executing custom code"""
        # Step 1: Generate with AI
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.return_value = "/tmp/model1.stl"

            response = client.post("/api/generate", json={"prompt": "Create a cube"})
            assert response.status_code == 200
            assert response.json()["success"] is True

        # Step 2: Execute custom code
        with (
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_exec.execute_and_export.return_value = "/tmp/model2.stl"

            response = client.post(
                "/api/execute",
                json={"code": "from badcad import *\nmodel = sphere(r=5)"},
            )
            assert response.status_code == 200
            assert response.json()["success"] is True


class TestAIFallbackWorkflow:
    """Test AI service failure and fallback mechanisms"""

    def test_gemini_failure_produces_fallback(self):
        """Test that AI failure produces fallback model"""
        failure_scenarios = [
            "RESOURCE_EXHAUSTED: quota",
            "PERMISSION_DENIED: auth",
            "INTERNAL_ERROR: general",
        ]

        for error_msg in failure_scenarios:
            with (
                patch("api.routes.generation.ai_generator") as mock_ai,
                patch("api.routes.generation.badcad_executor") as mock_exec,
                patch("api.routes.generation.model_storage"),
            ):
                from core.exceptions import AIGenerationError

                mock_ai.generate_badcad_code.side_effect = AIGenerationError(error_msg)
                mock_ai._generate_fallback_code.return_value = (
                    "from badcad import *\nmodel = cube(10, 10, 10)"
                )
                mock_exec.execute_and_export.return_value = "/tmp/fallback.stl"

                response = client.post(
                    "/api/generate",
                    json={"prompt": "Create a cone please"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "fallback" in data["message"].lower()

    def test_execution_failure_returns_error(self):
        """Test that execution failure returns appropriate error"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = complex_operation()"
            )
            mock_exec.execute_and_export.side_effect = Exception(
                "BadCAD execution error"
            )

            response = client.post(
                "/api/generate", json={"prompt": "Create complex model"}
            )

            assert response.status_code == 500


class TestConcurrentOperations:
    """Test concurrent operations"""

    def test_concurrent_model_generation(self):
        """Test multiple requests generating models concurrently"""
        import queue
        from threading import Thread

        results = queue.Queue()

        def generate_model(user_num):
            with (
                patch("api.routes.generation.ai_generator") as mock_ai,
                patch("api.routes.generation.badcad_executor") as mock_exec,
                patch("api.routes.generation.model_storage"),
            ):
                mock_ai.generate_badcad_code.return_value = (
                    f"from badcad import *\n"
                    f"model = cube({user_num},{user_num},{user_num})"
                )
                mock_exec.execute_and_export.return_value = (
                    f"/tmp/concurrent_{user_num}.stl"
                )

                response = client.post(
                    "/api/generate",
                    json={"prompt": f"Create cube number {user_num}"},
                )

                results.put((user_num, response.status_code, response.json()))

        # Start concurrent requests
        threads = []
        for i in range(5):
            t = Thread(target=generate_model, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify all succeeded
        successful_models = []
        while not results.empty():
            user_num, status, data = results.get()
            assert status == 200
            assert data["success"] is True
            successful_models.append(data["model_id"])

        # Verify all model IDs are unique
        assert len(successful_models) == len(set(successful_models))


class TestErrorRecovery:
    """Test error recovery and resilience"""

    def test_generate_with_execution_failure(self):
        """Test that execution failures are handled properly"""
        with (
            patch("api.routes.generation.ai_generator") as mock_ai,
            patch("api.routes.generation.badcad_executor") as mock_exec,
            patch("api.routes.generation.model_storage"),
        ):
            mock_ai.generate_badcad_code.return_value = (
                "from badcad import *\nmodel = cube(10,10,10)"
            )
            mock_exec.execute_and_export.side_effect = Exception("Disk error")

            response = client.post("/api/generate", json={"prompt": "Create a cube"})

            assert response.status_code == 500

    def test_download_missing_file(self):
        """Test downloading when model file has been deleted from disk"""
        model_id = "a" * 36

        with patch("api.routes.download.model_storage") as mock_storage:
            mock_storage.get_model_path.return_value = "/tmp/nonexistent_file.stl"
            mock_storage.delete_model.return_value = True

            response = client.get(f"/api/download/{model_id}")

            assert response.status_code == 404
            assert "Model not found" in response.json()["detail"]

    def test_admin_service_failure(self):
        """Test admin endpoint when user service fails"""
        with patch("api.routes.admin.user_manager") as mock_um:
            mock_um.get_all_users_summary.side_effect = Exception("Service unavailable")

            response = client.get("/api/admin/collected-emails")

            assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
