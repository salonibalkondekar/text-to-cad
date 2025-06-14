"""
Storage service for managing files and temporary models
"""
import os
import json
import uuid
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from core.config import settings
from core.exceptions import StorageError


class ModelStorage:
    """Manages temporary model storage with automatic cleanup"""
    
    def __init__(self, temp_dir: Optional[str] = None, cleanup_after_hours: int = 24):
        """
        Initialize the model storage.
        
        Args:
            temp_dir: Directory for temporary files (defaults to settings)
            cleanup_after_hours: Hours before automatic cleanup
        """
        self.temp_dir = Path(temp_dir or settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_after = timedelta(hours=cleanup_after_hours)
        
        # In-memory storage of model paths
        self._models: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def store_model(self, model_id: str, file_path: str) -> None:
        """
        Store a model file reference.
        
        Args:
            model_id: Unique identifier for the model
            file_path: Path to the model file
        """
        with self._lock:
            self._models[model_id] = {
                'path': file_path,
                'created_at': datetime.now(),
                'accessed_at': datetime.now()
            }
    
    def get_model_path(self, model_id: str) -> Optional[str]:
        """
        Get the path to a stored model.
        
        Args:
            model_id: Unique identifier for the model
            
        Returns:
            Path to the model file if it exists, None otherwise
        """
        with self._lock:
            model_info = self._models.get(model_id)
            if model_info:
                # Update access time
                model_info['accessed_at'] = datetime.now()
                path = model_info['path']
                
                # Verify file still exists
                if os.path.exists(path):
                    return path
                else:
                    # File was deleted externally
                    del self._models[model_id]
            
            return None
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model and its file.
        
        Args:
            model_id: Unique identifier for the model
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            model_info = self._models.get(model_id)
            if model_info:
                try:
                    if os.path.exists(model_info['path']):
                        os.remove(model_info['path'])
                except OSError:
                    pass  # File might already be deleted
                
                del self._models[model_id]
                return True
            
            return False
    
    def cleanup_old_models(self) -> int:
        """
        Remove models older than the cleanup threshold.
        
        Returns:
            Number of models cleaned up
        """
        count = 0
        now = datetime.now()
        
        with self._lock:
            models_to_delete = []
            
            for model_id, model_info in self._models.items():
                if now - model_info['created_at'] > self.cleanup_after:
                    models_to_delete.append(model_id)
            
            for model_id in models_to_delete:
                if self.delete_model(model_id):
                    count += 1
        
        return count
    
    def get_temp_file_path(self, prefix: str = "model_", suffix: str = ".stl") -> str:
        """
        Generate a unique temporary file path.
        
        Args:
            prefix: File name prefix
            suffix: File extension
            
        Returns:
            Path to a new temporary file
        """
        unique_id = str(uuid.uuid4())
        filename = f"{prefix}{unique_id}{suffix}"
        return str(self.temp_dir / filename)
    
    @contextmanager
    def temporary_model(self, model_id: Optional[str] = None):
        """
        Context manager for temporary model files.
        
        Yields:
            Tuple of (model_id, file_path)
        """
        if model_id is None:
            model_id = str(uuid.uuid4())
        
        file_path = self.get_temp_file_path()
        
        try:
            yield model_id, file_path
            # Store the model if context exits successfully
            if os.path.exists(file_path):
                self.store_model(model_id, file_path)
        except Exception:
            # Clean up on error
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            raise


class UserDataStorage:
    """Manages user data persistence with thread-safe JSON file operations"""
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize user data storage.
        
        Args:
            file_path: Path to the JSON file (defaults to settings)
        """
        self.file_path = file_path or settings.collected_emails_file
        self._lock = threading.RLock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the JSON file exists"""
        if not os.path.exists(self.file_path):
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        except Exception as e:
            raise StorageError(f"Failed to load user data: {str(e)}", "load")
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        try:
            # Write to temporary file first
            temp_file = f"{self.file_path}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.file_path)
        except Exception as e:
            raise StorageError(f"Failed to save user data: {str(e)}", "save")
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific user"""
        with self._lock:
            data = self._load_data()
            return data.get(user_id)
    
    def update_user_data(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Update data for a specific user"""
        with self._lock:
            data = self._load_data()
            data[user_id] = user_data
            self._save_data(data)
    
    def add_user_prompt(self, user_id: str, email: str, prompt: str, prompt_type: str = "generate") -> Dict[str, Any]:
        """Add a prompt to user's history"""
        with self._lock:
            data = self._load_data()
            
            if user_id not in data:
                data[user_id] = {
                    'email': email,
                    'prompts': [],
                    'model_count': 0,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
            
            # Add the prompt
            data[user_id]['prompts'].append({
                'prompt': prompt,
                'type': prompt_type,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update last activity
            data[user_id]['last_activity'] = datetime.now().isoformat()
            
            self._save_data(data)
            return data[user_id]
    
    def get_all_user_data(self) -> Dict[str, Any]:
        """Get all user data"""
        with self._lock:
            return self._load_data()
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete a user's data"""
        with self._lock:
            data = self._load_data()
            if user_id in data:
                del data[user_id]
                self._save_data(data)
                return True
            return False


# Global instances
model_storage = ModelStorage()
user_data_storage = UserDataStorage()