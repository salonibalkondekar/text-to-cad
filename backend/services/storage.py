"""
Storage service for managing files and temporary models
"""
import os
import uuid
import threading
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from core.config import settings


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
            True if model was deleted, False if not found
        """
        with self._lock:
            model_info = self._models.get(model_id)
            if model_info:
                # Delete the file
                try:
                    os.remove(model_info['path'])
                except OSError:
                    pass  # File may already be deleted
                
                # Remove from storage
                del self._models[model_id]
                return True
            
            return False
    
    def cleanup_old_models(self, force: bool = False) -> int:
        """
        Clean up old model files.
        
        Args:
            force: If True, delete all models regardless of age
            
        Returns:
            Number of models cleaned up
        """
        cleanup_count = 0
        current_time = datetime.now()
        
        with self._lock:
            models_to_delete = []
            
            for model_id, model_info in self._models.items():
                if force or (current_time - model_info['accessed_at']) > self.cleanup_after:
                    models_to_delete.append(model_id)
            
            for model_id in models_to_delete:
                if self.delete_model(model_id):
                    cleanup_count += 1
        
        return cleanup_count
    
    def get_temp_file_path(self, suffix: str = '.stl') -> str:
        """
        Get a path for a new temporary file.
        
        Args:
            suffix: File extension
            
        Returns:
            Path to the temporary file
        """
        filename = f"{uuid.uuid4()}{suffix}"
        return str(self.temp_dir / filename)
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        List all stored models with their metadata.
        
        Returns:
            Dictionary of model_id -> model info
        """
        with self._lock:
            return {
                model_id: {
                    'path': info['path'],
                    'created_at': info['created_at'].isoformat(),
                    'accessed_at': info['accessed_at'].isoformat()
                }
                for model_id, info in self._models.items()
            }
    
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


# Global instances
model_storage = ModelStorage()