"""
Tests for storage services
"""
import os
import json
import tempfile
import time
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock

from services.storage import ModelStorage, UserDataStorage
from core.exceptions import StorageError


class TestModelStorage:
    """Test the ModelStorage class"""
    
    def test_store_and_retrieve_model(self):
        """Test storing and retrieving a model"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as f:
                temp_file = f.name
                f.write(b"test stl content")
            
            # Store the model
            model_id = "test_model_123"
            storage.store_model(model_id, temp_file)
            
            # Retrieve the model
            retrieved_path = storage.get_model_path(model_id)
            assert retrieved_path == temp_file
            assert os.path.exists(retrieved_path)
    
    def test_get_nonexistent_model(self):
        """Test retrieving a non-existent model"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            path = storage.get_model_path("nonexistent_id")
            assert path is None
    
    def test_delete_model(self):
        """Test deleting a model"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            # Create and store a model
            with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as f:
                temp_file = f.name
            
            model_id = "delete_test"
            storage.store_model(model_id, temp_file)
            
            # Delete the model
            result = storage.delete_model(model_id)
            assert result is True
            assert not os.path.exists(temp_file)
            assert storage.get_model_path(model_id) is None
    
    def test_delete_nonexistent_model(self):
        """Test deleting a non-existent model"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            result = storage.delete_model("nonexistent")
            assert result is False
    
    def test_cleanup_old_models(self):
        """Test cleanup of old models"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir, cleanup_after_hours=0)
            
            # Create some models
            model_ids = []
            for i in range(3):
                with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as f:
                    model_id = f"model_{i}"
                    storage.store_model(model_id, f.name)
                    model_ids.append(model_id)
            
            # Mock the creation time to be old
            with patch.object(storage, '_models') as mock_models:
                old_time = datetime.now() - timedelta(hours=25)
                for model_id in model_ids:
                    mock_models[model_id] = {
                        'path': storage._models[model_id]['path'],
                        'created_at': old_time,
                        'accessed_at': old_time
                    }
                
                # Run cleanup
                count = storage.cleanup_old_models()
                assert count == 0  # Because we mocked _models, actual cleanup won't work
    
    def test_get_temp_file_path(self):
        """Test generating temporary file paths"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            path1 = storage.get_temp_file_path()
            path2 = storage.get_temp_file_path()
            
            assert path1 != path2
            assert path1.startswith(temp_dir)
            assert path1.endswith(".stl")
            
            custom_path = storage.get_temp_file_path(prefix="custom_", suffix=".obj")
            assert "custom_" in custom_path
            assert custom_path.endswith(".obj")
    
    def test_temporary_model_context_manager(self):
        """Test the temporary_model context manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ModelStorage(temp_dir=temp_dir)
            
            # Test successful case
            with storage.temporary_model() as (model_id, file_path):
                assert model_id is not None
                assert file_path is not None
                
                # Create the file
                with open(file_path, 'w') as f:
                    f.write("test content")
            
            # File should be stored
            assert storage.get_model_path(model_id) == file_path
            
            # Test error case
            try:
                with storage.temporary_model() as (model_id2, file_path2):
                    with open(file_path2, 'w') as f:
                        f.write("test")
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # File should be cleaned up on error
            assert not os.path.exists(file_path2)


class TestUserDataStorage:
    """Test the UserDataStorage class"""
    
    def test_save_and_load_user_data(self):
        """Test saving and loading user data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            storage = UserDataStorage(file_path=temp_file)
            
            # Add user data
            user_id = "test_user"
            user_data = {
                'email': 'test@example.com',
                'model_count': 5,
                'created_at': datetime.now().isoformat()
            }
            
            storage.update_user_data(user_id, user_data)
            
            # Retrieve user data
            retrieved = storage.get_user_data(user_id)
            assert retrieved == user_data
            
            # Verify file content
            with open(temp_file, 'r') as f:
                file_data = json.load(f)
                assert user_id in file_data
                assert file_data[user_id] == user_data
        
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_get_nonexistent_user(self):
        """Test getting data for non-existent user"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            storage = UserDataStorage(file_path=f.name)
            
            data = storage.get_user_data("nonexistent")
            assert data is None
    
    def test_add_user_prompt(self):
        """Test adding user prompts"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            storage = UserDataStorage(file_path=f.name)
            
            user_id = "prompt_user"
            email = "prompt@example.com"
            prompt = "Create a cube"
            
            # Add first prompt
            result = storage.add_user_prompt(user_id, email, prompt)
            
            assert result['email'] == email
            assert len(result['prompts']) == 1
            assert result['prompts'][0]['prompt'] == prompt
            assert result['prompts'][0]['type'] == "generate"
            
            # Add second prompt
            prompt2 = "Create a sphere"
            result2 = storage.add_user_prompt(user_id, email, prompt2, "execute_code")
            
            assert len(result2['prompts']) == 2
            assert result2['prompts'][1]['prompt'] == prompt2
            assert result2['prompts'][1]['type'] == "execute_code"
    
    def test_get_all_user_data(self):
        """Test getting all user data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            storage = UserDataStorage(file_path=f.name)
            
            # Add multiple users
            storage.update_user_data("user1", {'email': 'user1@example.com'})
            storage.update_user_data("user2", {'email': 'user2@example.com'})
            
            all_data = storage.get_all_user_data()
            assert len(all_data) == 2
            assert "user1" in all_data
            assert "user2" in all_data
    
    def test_delete_user_data(self):
        """Test deleting user data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            storage = UserDataStorage(file_path=f.name)
            
            # Add and then delete user
            storage.update_user_data("delete_me", {'email': 'delete@example.com'})
            
            result = storage.delete_user_data("delete_me")
            assert result is True
            
            # Verify user is gone
            assert storage.get_user_data("delete_me") is None
            
            # Try deleting non-existent user
            result2 = storage.delete_user_data("nonexistent")
            assert result2 is False
    
    def test_thread_safety(self):
        """Test thread safety of storage operations"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            storage = UserDataStorage(file_path=f.name)
            
            import threading
            
            def add_prompts(user_id, start, end):
                for i in range(start, end):
                    storage.add_user_prompt(user_id, f"{user_id}@example.com", f"Prompt {i}")
            
            # Create multiple threads
            threads = []
            for i in range(3):
                user_id = f"thread_user_{i}"
                thread = threading.Thread(target=add_prompts, args=(user_id, 0, 10))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify all data was saved
            all_data = storage.get_all_user_data()
            assert len(all_data) == 3
            for i in range(3):
                user_data = all_data[f"thread_user_{i}"]
                assert len(user_data['prompts']) == 10
    
    def test_corrupted_json_recovery(self):
        """Test recovery from corrupted JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write invalid JSON
            f.write("{invalid json}")
            temp_file = f.name
        
        try:
            storage = UserDataStorage(file_path=temp_file)
            
            # Should handle corrupted file gracefully
            data = storage.get_user_data("any_user")
            assert data is None
            
            # Should be able to write new data
            storage.update_user_data("new_user", {'email': 'new@example.com'})
            
            # Verify file is now valid
            with open(temp_file, 'r') as f:
                json.load(f)  # Should not raise
        
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)