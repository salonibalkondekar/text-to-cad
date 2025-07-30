"""
API routes for admin functionality
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from core.models import AdminSummaryResponse
from core.config import settings
from services.user_management import user_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Security scheme for admin endpoints (future enhancement)
security = HTTPBearer(auto_error=False)


async def verify_admin_access(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    Verify admin access credentials.

    Currently a placeholder for future authentication implementation.
    In production, this should verify API keys, JWT tokens, etc.
    """
    # TODO: Implement proper admin authentication
    # For now, we'll check if admin API key is configured
    if settings.enable_auth and settings.admin_api_key:
        if not credentials or credentials.credentials != settings.admin_api_key:
            raise HTTPException(status_code=401, detail="Admin authentication required")

    # Log admin access attempts
    token = credentials.credentials[:10] + "..." if credentials else "None"
    logger.warning(f"Admin access attempt with token: {token}")

    return True


@router.get("/collected-emails", response_model=AdminSummaryResponse)
async def get_collected_emails(admin_verified: bool = Depends(verify_admin_access)):
    """
    Admin endpoint to view collected user data and usage statistics.

    Returns comprehensive information about all users, their prompts,
    and model generation activity.

    Note: This endpoint should be secured in production environments.
    """
    try:
        logger.info("Admin data summary requested")

        # Get comprehensive user summary from user manager
        summary_data = user_manager.get_all_users_summary()

        # Convert to response model format
        return AdminSummaryResponse(
            total_users=summary_data["total_users"],
            total_prompts=summary_data["total_prompts"],
            total_models_generated=summary_data["total_models_generated"],
            users=summary_data["users"],
        )

    except Exception as e:
        logger.error(f"Error in get_collected_emails: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/user/{user_id}")
async def delete_user(
    user_id: str, admin_verified: bool = Depends(verify_admin_access)
):
    """
    Admin endpoint to delete a user and all their data.

    This is a destructive operation that removes all user information,
    prompts, and resets their model count.
    """
    try:
        logger.warning(f"Admin deletion request for user: {user_id}")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # Delete the user
        deleted = user_manager.delete_user(user_id)

        if deleted:
            logger.info(f"User {user_id} successfully deleted by admin")
            return {"success": True, "message": f"User {user_id} deleted"}
        else:
            logger.warning(f"User {user_id} not found for deletion")
            raise HTTPException(status_code=404, detail="User not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/{user_id}/reset-count")
async def reset_user_count(
    user_id: str, admin_verified: bool = Depends(verify_admin_access)
):
    """
    Admin endpoint to reset a user's model generation count.

    This allows an admin to reset a user's count back to zero,
    effectively giving them a fresh allocation of models.
    """
    try:
        logger.warning(f"Admin count reset request for user: {user_id}")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # Check if user exists
        user_data = user_manager.get_user(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Reset the count
        user_manager.reset_user_count(user_id)

        logger.info(f"User {user_id} count reset to 0 by admin")
        return {"success": True, "message": f"User {user_id} count reset to 0"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_user_count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
