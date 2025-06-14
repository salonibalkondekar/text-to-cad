"""
API routes for user management functionality
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from core.models import (
    UserInfoRequest, UserCountRequest, UserInfoResponse, UserCountResponse
)
from core.exceptions import UserLimitExceededError, AuthorizationError
from services.analytics_client import analytics_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/info", response_model=UserInfoResponse)
async def get_user_info(request: UserInfoRequest, http_request: Request, response: Response):
    """
    Create or update user information and return current status.
    
    This endpoint registers a new user or updates existing user information,
    then returns their current model count and limits.
    """
    try:
        logger.info(f"User info request for: {request.user_id} ({request.email})")
        
        # Validate input
        if not request.user_id or not request.email or not request.name:
            raise HTTPException(status_code=400, detail="Missing required user information")
        
        # Create session in analytics service
        session_data = await analytics_client.create_session(
            email=request.email,
            name=request.name,
            request_headers=dict(http_request.headers)
        )
        
        # Set session cookie
        if "csrf_token" in session_data:
            response.set_cookie(
                key="session_id",
                value=session_data.get("session_id", ""),
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=7 * 24 * 3600  # 7 days
            )
        
        logger.info(f"User data updated for {request.user_id}: {session_data['user']['model_count']} models")
        
        return UserInfoResponse(
            success=True,
            user_id=request.user_id,
            model_count=session_data['user']['model_count'],
            max_models=10  # Hardcoded for now
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/increment-count", response_model=UserCountResponse)
async def increment_user_count(request: UserCountRequest, http_request: Request):
    """
    Increment a user's model generation count.
    
    This is typically called after successful model generation to track
    usage against the user's limits.
    """
    try:
        logger.info(f"Incrementing count for user: {request.user_id}")
        
        # Validate input
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get session cookie
        session_cookie = http_request.cookies.get("session_id")
        if not session_cookie:
            raise HTTPException(status_code=401, detail="No session found")
        
        # Increment the count via analytics service
        try:
            result = await analytics_client.increment_user_count(
                user_id=request.user_id,
                session_cookie=session_cookie
            )
            
            logger.info(f"User {request.user_id} count incremented to: {result['model_count']}")
            
            return UserCountResponse(
                success=True,
                model_count=result['model_count']
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(f"User {request.user_id} exceeded limit")
                raise HTTPException(
                    status_code=403, 
                    detail="Model generation limit exceeded"
                )
            elif e.response.status_code == 404:
                logger.warning(f"User {request.user_id} not found")
                raise HTTPException(
                    status_code=404, 
                    detail="User not found"
                )
            else:
                raise
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in increment_user_count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")