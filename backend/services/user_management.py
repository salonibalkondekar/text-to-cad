"""
Modern user management service using analytics backend
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.config import settings
from core.exceptions import UserLimitExceededError, AuthorizationError
from services.analytics_client import analytics_client

logger = logging.getLogger(__name__)


class ModernUserManager:
    """Manages users through the analytics service"""
    
    def __init__(self, max_models_per_user: Optional[int] = None):
        """
        Initialize the user manager.
        
        Args:
            max_models_per_user: Maximum models per user (defaults to settings)
        """
        self.max_models_per_user = max_models_per_user or settings.max_models_per_user
        self.analytics_client = analytics_client
    
    async def create_or_get_session(
        self, 
        email: str, 
        name: str,
        request_headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Create a new session and user in analytics service.
        
        Args:
            email: User's email address
            name: User's name
            request_headers: HTTP headers from request
            
        Returns:
            Session information including user_id and session_id
        """
        try:
            result = await self.analytics_client.create_session(
                email=email,
                name=name,
                request_headers=request_headers
            )
            logger.info(f"Created session for user: {email}")
            return result
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise AuthorizationError(f"Failed to create session: {str(e)}")
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from analytics service.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User information or None if not found
        """
        try:
            return await self.analytics_client.get_user_info(user_id)
        except Exception as e:
            logger.warning(f"Failed to get user info for {user_id}: {str(e)}")
            return None
    
    async def check_user_limit(self, user_id: str) -> bool:
        """
        Check if user has reached their model generation limit.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if user can generate more models
            
        Raises:
            UserLimitExceededError: If user has reached their limit
        """
        user_info = await self.get_user_info(user_id)
        
        if not user_info:
            # New user, allow generation
            return True
        
        model_count = user_info.get('model_count', 0)
        if model_count >= self.max_models_per_user:
            raise UserLimitExceededError(
                f"Model generation limit ({self.max_models_per_user}) reached",
                user_id=user_id,
                limit=self.max_models_per_user,
                current=model_count
            )
        
        return True
    
    async def increment_model_count(
        self, 
        user_id: str,
        session_cookie: str
    ) -> Dict[str, Any]:
        """
        Increment user's model count after successful generation.
        
        Args:
            user_id: User's unique identifier
            session_cookie: Session cookie for authentication
            
        Returns:
            Updated user information
        """
        try:
            result = await self.analytics_client.increment_user_count(
                user_id=user_id,
                session_cookie=session_cookie
            )
            logger.info(f"Incremented model count for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to increment model count: {str(e)}")
            # Don't fail the generation if we can't increment count
            return {"model_count": 0}
    
    async def track_generation(
        self,
        session_cookie: str,
        prompt: str,
        success: bool,
        error_message: Optional[str] = None,
        generation_time: Optional[float] = None
    ) -> None:
        """
        Track a CAD generation event.
        
        Args:
            session_cookie: Session cookie for authentication
            prompt: The generation prompt
            success: Whether generation succeeded
            error_message: Error message if failed
            generation_time: Time taken for generation
        """
        try:
            await self.analytics_client.track_cad_event(
                session_cookie=session_cookie,
                event_data={
                    "event_type": "generate",
                    "prompt": prompt,
                    "success": success,
                    "error_message": error_message,
                    "generation_time": generation_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track generation event: {str(e)}")
            # Don't fail the request if tracking fails


# Global user manager instance
user_manager = ModernUserManager()