"""
Tests for user management service
"""

from unittest.mock import patch

import pytest

from core.exceptions import AuthorizationError, UserLimitExceededError
from services.user_management import UserManager


class TestUserManager:
    """Test the UserManager class"""

    @patch("services.user_management.user_data_storage")
    def test_create_new_user(self, mock_storage):
        """Test creating a new user"""
        mock_storage.get_all_user_data.return_value = {}

        manager = UserManager(max_models_per_user=10)

        user_id = "new_user_123"
        email = "new@example.com"
        name = "New User"

        result = manager.create_or_update_user(user_id, email, name)

        assert result["email"] == email
        assert result["name"] == name
        assert result["model_count"] == 0
        assert "created_at" in result
        assert "last_login" in result

        # Verify storage was updated
        mock_storage.update_user_data.assert_called_once()

    @patch("services.user_management.user_data_storage")
    def test_update_existing_user(self, mock_storage):
        """Test updating an existing user"""
        mock_storage.get_all_user_data.return_value = {
            "existing_user": {
                "email": "old@example.com",
                "name": "Old Name",
                "model_count": 5,
            }
        }

        manager = UserManager()
        manager._load_users_from_storage()

        user_id = "existing_user"
        new_email = "new@example.com"
        new_name = "New Name"

        result = manager.create_or_update_user(user_id, new_email, new_name)

        assert result["email"] == new_email
        assert result["name"] == new_name
        assert result["model_count"] == 5  # Should preserve count

    def test_get_user(self):
        """Test getting user information"""
        manager = UserManager()

        # Add a user
        user_id = "get_test"
        manager._users[user_id] = {
            "email": "test@example.com",
            "name": "Test User",
            "model_count": 3,
        }

        # Get existing user
        user = manager.get_user(user_id)
        assert user["email"] == "test@example.com"
        assert user["model_count"] == 3

        # Get non-existent user
        user = manager.get_user("nonexistent")
        assert user is None

    def test_check_user_can_generate(self):
        """Test checking if user can generate models"""
        manager = UserManager(max_models_per_user=5)

        # New user can generate
        assert manager.check_user_can_generate("new_user") is True

        # User under limit can generate
        manager._users["under_limit"] = {"model_count": 3}
        assert manager.check_user_can_generate("under_limit") is True

        # User at limit cannot generate
        manager._users["at_limit"] = {"model_count": 5}
        assert manager.check_user_can_generate("at_limit") is False

    @patch("services.user_management.user_data_storage")
    def test_increment_user_model_count(self, mock_storage):
        """Test incrementing user model count"""
        mock_storage.get_user_data.return_value = {"model_count": 2}

        manager = UserManager(max_models_per_user=5)
        manager._users["test_user"] = {"email": "test@example.com", "model_count": 2}

        # Increment count
        new_count = manager.increment_user_model_count("test_user")
        assert new_count == 3
        assert manager._users["test_user"]["model_count"] == 3

        # Verify storage was updated
        mock_storage.update_user_data.assert_called()

    def test_increment_at_limit_raises_error(self):
        """Test incrementing when at limit raises error"""
        manager = UserManager(max_models_per_user=3)
        manager._users["limited_user"] = {
            "email": "limited@example.com",
            "model_count": 3,
        }

        with pytest.raises(UserLimitExceededError) as exc_info:
            manager.increment_user_model_count("limited_user")

        assert exc_info.value.status_code == 403
        assert "limit reached" in exc_info.value.message.lower()

    def test_increment_nonexistent_user_raises_error(self):
        """Test incrementing for non-existent user raises error"""
        manager = UserManager()

        with pytest.raises(AuthorizationError) as exc_info:
            manager.increment_user_model_count("ghost_user")

        assert "not found" in exc_info.value.message

    def test_get_user_model_count(self):
        """Test getting user's model count"""
        manager = UserManager()

        manager._users["counted_user"] = {"model_count": 7}

        assert manager.get_user_model_count("counted_user") == 7
        assert manager.get_user_model_count("nonexistent") == 0

    @patch("services.user_management.user_data_storage")
    def test_record_user_prompt(self, mock_storage):
        """Test recording user prompts"""
        manager = UserManager()
        manager._users["prompt_user"] = {"email": "prompt@example.com"}

        manager.record_user_prompt("prompt_user", "Create a cube", "generate")

        mock_storage.add_user_prompt.assert_called_once_with(
            "prompt_user", "prompt@example.com", "Create a cube", "generate"
        )

        # Test with non-existent user (should not record)
        manager.record_user_prompt("nonexistent", "Test", "generate")
        assert mock_storage.add_user_prompt.call_count == 1  # Still 1

    @patch("services.user_management.user_data_storage")
    def test_get_all_users_summary(self, mock_storage):
        """Test getting summary of all users"""
        mock_storage.get_all_user_data.return_value = {
            "user1": {
                "email": "user1@example.com",
                "name": "User One",
                "model_count": 3,
                "prompts": [
                    {"prompt": "Test 1", "type": "generate"},
                    {"prompt": "Test 2", "type": "generate"},
                ],
                "created_at": "2024-01-01",
                "last_activity": "2024-01-02",
            },
            "user2": {
                "email": "user2@example.com",
                "model_count": 1,
                "prompts": [{"prompt": "Test 3", "type": "execute_code"}],
            },
        }

        manager = UserManager()
        summary = manager.get_all_users_summary()

        assert summary["total_users"] == 2
        assert summary["total_prompts"] == 3
        assert summary["total_models_generated"] == 4
        assert len(summary["users"]) == 2

        # Check user details
        user1_summary = next(u for u in summary["users"] if u["user_id"] == "user1")
        assert user1_summary["email"] == "user1@example.com"
        assert user1_summary["total_prompts"] == 2
        assert len(user1_summary["recent_prompts"]) == 2

    @patch("services.user_management.user_data_storage")
    def test_reset_user_count(self, mock_storage):
        """Test resetting user's model count"""
        mock_storage.get_user_data.return_value = {"model_count": 10}

        manager = UserManager()
        manager._users["reset_user"] = {"model_count": 10}

        manager.reset_user_count("reset_user")

        assert manager._users["reset_user"]["model_count"] == 0
        mock_storage.update_user_data.assert_called()

    @patch("services.user_management.user_data_storage")
    def test_delete_user(self, mock_storage):
        """Test deleting a user"""
        manager = UserManager()
        manager._users["delete_me"] = {"email": "delete@example.com"}

        # Delete existing user
        result = manager.delete_user("delete_me")
        assert result is True
        assert "delete_me" not in manager._users
        mock_storage.delete_user_data.assert_called_once_with("delete_me")

        # Delete non-existent user
        result = manager.delete_user("nonexistent")
        assert result is False

    @patch("services.user_management.user_data_storage")
    def test_load_users_from_storage(self, mock_storage):
        """Test loading users from storage on initialization"""
        mock_storage.get_all_user_data.return_value = {
            "stored_user": {
                "email": "stored@example.com",
                "name": "Stored User",
                "model_count": 5,
                "created_at": "2024-01-01",
                "last_activity": "2024-01-02",
            }
        }

        manager = UserManager()

        assert "stored_user" in manager._users
        assert manager._users["stored_user"]["email"] == "stored@example.com"
        assert manager._users["stored_user"]["model_count"] == 5
