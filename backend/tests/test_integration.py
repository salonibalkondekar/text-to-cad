"""
Integration tests for the Text-to-CAD API
Tests complete workflows and interactions between components
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies
with patch("app.load_dotenv"):
    with patch("app.badcad"):
        with patch("app.genai"):
            from app import app, temp_models, user_database

client = TestClient(app)


class TestCompleteUserWorkflow:
    """Test complete user workflows from registration to model generation"""

    def test_new_user_complete_workflow(self):
        """Test complete workflow for a new user"""
        user_id = "workflow_user_123"
        email = "workflow@example.com"

        # Step 1: Register new user
        response = client.post(
            "/api/user/info",
            json={"user_id": user_id, "email": email, "name": "Workflow User"},
        )
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["model_count"] == 0

        # Step 2: Generate first model
        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/model1.stl"

                response = client.post(
                    "/api/generate",
                    json={"prompt": "Create a cube", "user_id": user_id},
                )
                assert response.status_code == 200
                model_data = response.json()
                model_id = model_data["model_id"]

        # Step 3: Check updated user info
        response = client.post(
            "/api/user/info",
            json={"user_id": user_id, "email": email, "name": "Workflow User"},
        )
        assert response.status_code == 200
        assert response.json()["model_count"] == 1

        # Step 4: Download the model
        temp_models[model_id] = "/tmp/model1.stl"
        # Create actual file for download test
        with open("/tmp/model1.stl", "w") as f:
            f.write("solid test\nendsolid test")

        try:
            response = client.get(f"/api/download/{model_id}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
        finally:
            if os.path.exists("/tmp/model1.stl"):
                os.unlink("/tmp/model1.stl")

        # Step 5: Execute custom BadCAD code
        with patch("app.execute_badcad_and_export") as mock_execute:
            mock_execute.return_value = "/tmp/model2.stl"

            response = client.post(
                "/api/execute",
                json={
                    "code": "from badcad import *\nmodel = sphere(r=5)",
                    "user_id": user_id,
                },
            )
            assert response.status_code == 200

        # Step 6: Verify model count increased
        assert user_database[user_id]["model_count"] == 2

    def test_user_reaching_limit_workflow(self):
        """Test workflow when user reaches generation limit"""
        user_id = "limit_workflow_user"

        # Set up user near limit
        user_database[user_id] = {
            "email": "limit@example.com",
            "name": "Limit User",
            "model_count": 9,
        }

        # Generate one more model (should succeed)
        with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
            with patch("app.execute_badcad_and_export") as mock_execute:
                mock_gemini.return_value = (
                    "from badcad import *\nmodel = cube(10,10,10)"
                )
                mock_execute.return_value = "/tmp/model_limit.stl"

                response = client.post(
                    "/api/generate",
                    json={"prompt": "Create final cube", "user_id": user_id},
                )
                assert response.status_code == 200

        # Try to generate another (should fail)
        response = client.post(
            "/api/generate", json={"prompt": "Create one more cube", "user_id": user_id}
        )
        assert response.status_code == 403
        assert "limit reached" in response.json()["detail"]

        # Also test execute endpoint
        response = client.post(
            "/api/execute",
            json={
                "code": "from badcad import *\nmodel = cube(5,5,5)",
                "user_id": user_id,
            },
        )
        assert response.status_code == 403


class TestAIFallbackWorkflow:
    """Test AI service failure and fallback mechanisms"""

    def test_gemini_failure_fallback_workflow(self):
        """Test complete workflow when Gemini AI fails"""
        # Simulate different types of Gemini failures
        failure_scenarios = [
            ("RESOURCE_EXHAUSTED", "quota"),
            ("PERMISSION_DENIED", "auth"),
            ("INTERNAL_ERROR", "general"),
            ("NETWORK_ERROR", "connection"),
        ]

        for error_type, error_msg in failure_scenarios:
            with patch("app.GEMINI_AVAILABLE", True):
                with patch("app.gemini_client") as mock_client:
                    # Simulate API failure
                    mock_client.models.generate_content.side_effect = Exception(
                        f"{error_type}: {error_msg}"
                    )

                    with patch("app.execute_badcad_and_export") as mock_execute:
                        mock_execute.return_value = f"/tmp/fallback_{error_type}.stl"

                        response = client.post(
                            "/api/generate", json={"prompt": "Create a cone please"}
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert "fallback" in data["message"].lower()
                        # Should use smart fallback for "cone"
                        assert (
                            "cone" in data["badcad_code"]
                            or "extrude_to" in data["badcad_code"]
                        )

    def test_badcad_failure_fallback_workflow(self):
        """Test workflow when BadCAD execution fails"""
        with patch("app.BADCAD_AVAILABLE", True):
            with patch("builtins.exec") as mock_exec:
                # Simulate execution failure
                mock_exec.side_effect = Exception("BadCAD execution error")

                with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                    mock_gemini.return_value = (
                        "from badcad import *\nmodel = complex_operation()"
                    )

                    response = client.post(
                        "/api/generate", json={"prompt": "Create complex model"}
                    )

                    assert response.status_code == 200
                    # Should still return a model ID (with fallback STL)


class TestDataPersistenceIntegration:
    """Test data persistence across operations"""

    def test_user_data_persistence(self):
        """Test that user data persists correctly"""
        user_id = "persist_user_123"

        with patch("app.load_collected_emails") as mock_load:
            with patch("app.save_collected_emails") as mock_save:
                mock_load.return_value = {}
                saved_data = {}

                def save_side_effect(data):
                    saved_data.update(data)

                mock_save.side_effect = save_side_effect

                # Create user
                response = client.post(
                    "/api/user/info",
                    json={
                        "user_id": user_id,
                        "email": "persist@example.com",
                        "name": "Persist User",
                    },
                )
                assert response.status_code == 200

                # Generate model with prompt tracking
                with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                    with patch("app.execute_badcad_and_export") as mock_execute:
                        mock_gemini.return_value = (
                            "from badcad import *\nmodel = cube(10,10,10)"
                        )
                        mock_execute.return_value = "/tmp/persist.stl"

                        response = client.post(
                            "/api/generate",
                            json={
                                "prompt": "Create a persistent cube",
                                "user_id": user_id,
                            },
                        )
                        assert response.status_code == 200

                # Verify data was saved
                assert mock_save.called
                assert user_id in saved_data
                assert len(saved_data[user_id]["prompts"]) > 0
                assert (
                    saved_data[user_id]["prompts"][0]["prompt"]
                    == "Create a persistent cube"
                )

    def test_admin_endpoint_data_aggregation(self):
        """Test admin endpoint aggregates data correctly"""
        # Set up test data
        test_data = {
            "user1": {
                "email": "user1@test.com",
                "name": "User One",
                "model_count": 5,
                "prompts": [
                    {"prompt": "cube", "type": "generate"},
                    {"prompt": "sphere", "type": "generate"},
                ],
            },
            "user2": {
                "email": "user2@test.com",
                "name": "User Two",
                "model_count": 3,
                "prompts": [{"prompt": "cylinder", "type": "generate"}],
            },
        }

        with patch("app.load_collected_emails") as mock_load:
            mock_load.return_value = test_data

            response = client.get("/api/admin/collected-emails")
            assert response.status_code == 200

            summary = response.json()
            assert summary["total_users"] == 2
            assert summary["total_prompts"] == 3
            assert summary["total_models_generated"] == 8

            # Verify user details
            users_by_id = {u["user_id"]: u for u in summary["users"]}
            assert users_by_id["user1"]["total_prompts"] == 2
            assert users_by_id["user2"]["total_prompts"] == 1


class TestConcurrentOperations:
    """Test concurrent operations and race conditions"""

    def test_concurrent_model_generation(self):
        """Test multiple users generating models concurrently"""
        import queue
        from threading import Thread

        results = queue.Queue()

        def generate_model(user_num):
            with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                with patch("app.execute_badcad_and_export") as mock_execute:
                    mock_gemini.return_value = f"from badcad import *\nmodel = cube({user_num},{user_num},{user_num})"
                    mock_execute.return_value = f"/tmp/concurrent_{user_num}.stl"

                    response = client.post(
                        "/api/generate",
                        json={
                            "prompt": f"Create cube number {user_num}",
                            "user_id": f"concurrent_user_{user_num}",
                        },
                    )

                    results.put((user_num, response.status_code, response.json()))

        # Start 10 concurrent requests
        threads = []
        for i in range(10):
            t = Thread(target=generate_model, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
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

    def test_concurrent_user_updates(self):
        """Test concurrent updates to same user"""
        user_id = "concurrent_update_user"

        # Initialize user
        user_database[user_id] = {
            "email": "concurrent@test.com",
            "name": "Concurrent User",
            "model_count": 0,
        }

        import queue
        from threading import Thread

        results = queue.Queue()

        def update_user(operation_num):
            # Alternate between generate and increment operations
            if operation_num % 2 == 0:
                response = client.post(
                    "/api/user/increment-count", json={"user_id": user_id}
                )
            else:
                with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                    with patch("app.execute_badcad_and_export") as mock_execute:
                        mock_gemini.return_value = (
                            "from badcad import *\nmodel = cube(5,5,5)"
                        )
                        mock_execute.return_value = (
                            f"/tmp/concurrent_op_{operation_num}.stl"
                        )

                        response = client.post(
                            "/api/generate",
                            json={"prompt": "Concurrent cube", "user_id": user_id},
                        )

            results.put((operation_num, response.status_code))

        # Start concurrent operations
        threads = []
        for i in range(20):
            t = Thread(target=update_user, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Count successes
        success_count = 0
        while not results.empty():
            _, status = results.get()
            if status == 200:
                success_count += 1

        # Should have at most 10 successful operations due to limit
        assert success_count <= 10
        assert user_database[user_id]["model_count"] <= 10


class TestErrorRecovery:
    """Test error recovery and resilience"""

    def test_recovery_from_corrupted_json_file(self):
        """Test recovery when JSON file is corrupted"""
        with patch("app.load_collected_emails") as mock_load:
            # Simulate corrupted file
            mock_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            # Should handle gracefully and return empty data
            client.get("/api/admin/collected-emails")
            # Current implementation would fail - this documents the issue

    def test_recovery_from_disk_full(self):
        """Test handling when disk is full"""
        with patch("app.save_collected_emails") as mock_save:
            mock_save.side_effect = OSError("No space left on device")

            # Operations should still work (in-memory)
            response = client.post(
                "/api/user/info",
                json={
                    "user_id": "disk_full_user",
                    "email": "diskfull@test.com",
                    "name": "Disk Full User",
                },
            )

            assert response.status_code == 200
            # Data saved to memory even if file write fails

    def test_stl_file_cleanup(self):
        """Test that temporary STL files are managed properly"""
        model_ids = []

        # Generate multiple models
        for i in range(5):
            with patch("app.generate_badcad_code_with_gemini") as mock_gemini:
                with patch("app.execute_badcad_and_export") as mock_execute:
                    mock_gemini.return_value = (
                        "from badcad import *\nmodel = cube(10,10,10)"
                    )
                    mock_execute.return_value = f"/tmp/cleanup_test_{i}.stl"

                    response = client.post(
                        "/api/generate", json={"prompt": f"Create cube {i}"}
                    )

                    assert response.status_code == 200
                    model_ids.append(response.json()["model_id"])

        # Verify all models are tracked
        assert len(temp_models) >= 5

        # Note: Current implementation doesn't clean up old files
        # This test documents that limitation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
