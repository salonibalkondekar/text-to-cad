"""
User management service for tracking users and their model generation limits
"""
import threading
from typing import Dict, Optional, Any
from datetime import datetime

from core.config import settings
from core.models import UserData
from core.exceptions import UserLimitExceededError, AuthorizationError
from services.storage import user_data_storage


class UserManager:
    """Manages user accounts and model generation limits"""
    
    def __init__(self, max_models_per_user: Optional[int] = None):
        """
        Initialize the user manager.
        
        Args:
            max_models_per_user: Maximum models per user (defaults to settings)
        """
        self.max_models_per_user = max_models_per_user or settings.max_models_per_user
        
        # In-memory user database for fast access
        self._users: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Load existing users from storage
        self._load_users_from_storage()
    
    def _load_users_from_storage(self):
        """Load users from persistent storage"""
        try:
            all_users = user_data_storage.get_all_user_data()
            with self._lock:
                for user_id, user_data in all_users.items():
                    self._users[user_id] = {
                        'email': user_data.get('email', 'unknown@example.com'),
                        'name': user_data.get('name', 'Unknown'),
                        'model_count': user_data.get('model_count', 0),
                        'created_at': user_data.get('created_at', datetime.now().isoformat()),
                        'last_login': user_data.get('last_activity', datetime.now().isoformat())
                    }
        except Exception:
            # If loading fails, start with empty user database
            pass
    
    def create_or_update_user(self, user_id: str, email: str, name: str) -> Dict[str, Any]:
        """
        Create a new user or update existing user information.
        
        Args:
            user_id: Unique identifier for the user
            email: User's email address
            name: User's name
            
        Returns:
            User information dictionary
        """
        with self._lock:
            if user_id not in self._users:
                # Create new user
                self._users[user_id] = {
                    'email': email,
                    'name': name,
                    'model_count': 0,
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat()
                }
                
                # Also create in persistent storage
                user_data_storage.update_user_data(user_id, {
                    'email': email,
                    'name': name,
                    'prompts': [],
                    'model_count': 0,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                })
            else:
                # Update existing user
                self._users[user_id].update({
                    'email': email,
                    'name': name,
                    'last_login': datetime.now().isoformat()
                })
                
                # Update persistent storage
                existing_data = user_data_storage.get_user_data(user_id) or {}
                existing_data.update({
                    'email': email,
                    'name': name,
                    'last_activity': datetime.now().isoformat()
                })
                user_data_storage.update_user_data(user_id, existing_data)
            
            return self._users[user_id].copy()
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            User information if found, None otherwise
        """
        with self._lock:
            return self._users.get(user_id, {}).copy() if user_id in self._users else None
    
    def check_user_can_generate(self, user_id: str) -> bool:
        """
        Check if a user can generate more models.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if user can generate, False otherwise
        """
        with self._lock:
            if user_id not in self._users:
                return True  # New users can generate
            
            return self._users[user_id]['model_count'] < self.max_models_per_user
    
    def increment_user_model_count(self, user_id: str) -> int:
        """
        Increment a user's model count.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Updated model count
            
        Raises:
            UserLimitExceededError: If user is at the limit
        """
        with self._lock:
            if user_id not in self._users:
                # User doesn't exist, this shouldn't happen in normal flow
                raise AuthorizationError(f"User {user_id} not found")
            
            user = self._users[user_id]
            
            if user['model_count'] >= self.max_models_per_user:
                raise UserLimitExceededError(
                    user_id=user_id,
                    current_count=user['model_count'],
                    max_count=self.max_models_per_user
                )
            
            # Increment count
            user['model_count'] += 1
            
            # Update persistent storage
            existing_data = user_data_storage.get_user_data(user_id) or {}
            existing_data['model_count'] = user['model_count']
            existing_data['last_activity'] = datetime.now().isoformat()
            user_data_storage.update_user_data(user_id, existing_data)
            
            return user['model_count']
    
    def get_user_model_count(self, user_id: str) -> int:
        """
        Get a user's current model count.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Current model count (0 if user doesn't exist)
        """
        with self._lock:
            if user_id in self._users:
                return self._users[user_id]['model_count']
            return 0
    
    def record_user_prompt(self, user_id: str, prompt: str, prompt_type: str = "generate") -> None:
        """
        Record a user's prompt in persistent storage.
        
        Args:
            user_id: Unique identifier for the user
            prompt: The prompt text
            prompt_type: Type of prompt (generate or execute_code)
        """
        if user_id and user_id in self._users:
            email = self._users[user_id].get('email', 'unknown@example.com')
            user_data_storage.add_user_prompt(user_id, email, prompt, prompt_type)
    
    def get_all_users_summary(self) -> Dict[str, Any]:
        """
        Get summary information for all users.
        
        Returns:
            Dictionary with user statistics
        """
        with self._lock:
            # Get full data from storage for complete statistics
            all_user_data = user_data_storage.get_all_user_data()
            
            summary = {
                'total_users': len(all_user_data),
                'total_prompts': sum(
                    len(user_data.get('prompts', [])) 
                    for user_data in all_user_data.values()
                ),
                'total_models_generated': sum(
                    user_data.get('model_count', 0) 
                    for user_data in all_user_data.values()
                ),
                'users': []
            }
            
            for user_id, user_data in all_user_data.items():
                prompts = user_data.get('prompts', [])
                summary['users'].append({
                    'user_id': user_id,
                    'email': user_data.get('email', 'N/A'),
                    'name': user_data.get('name', 'N/A'),
                    'model_count': user_data.get('model_count', 0),
                    'total_prompts': len(prompts),
                    'created_at': user_data.get('created_at', 'N/A'),
                    'last_activity': user_data.get('last_activity', 'N/A'),
                    'recent_prompts': prompts[-3:] if prompts else []
                })
            
            return summary
    
    def reset_user_count(self, user_id: str) -> None:
        """
        Reset a user's model count (admin function).
        
        Args:
            user_id: Unique identifier for the user
        """
        with self._lock:
            if user_id in self._users:
                self._users[user_id]['model_count'] = 0
                
                # Update persistent storage
                existing_data = user_data_storage.get_user_data(user_id) or {}
                existing_data['model_count'] = 0
                user_data_storage.update_user_data(user_id, existing_data)
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (admin function).
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if user_id in self._users:
                del self._users[user_id]
                user_data_storage.delete_user_data(user_id)
                return True
            return False


# Global instance
user_manager = UserManager()