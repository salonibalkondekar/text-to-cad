"""
API routes for file download functionality
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from services.storage import model_storage
from services.user_management import user_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download/{model_id}")
async def download_model(model_id: str):
    """
    Download the STL file for a generated model.

    Args:
        model_id: The unique identifier for the model to download

    Returns:
        FileResponse with the STL file for download

    Raises:
        HTTPException: 404 if model not found
    """
    try:
        logger.info(f"Download requested for model: {model_id}")

        # Validate model_id format (basic security check)
        if not model_id or len(model_id) < 10:  # UUIDs are much longer
            raise HTTPException(status_code=404, detail="Model not found")

        # Get the model file path
        stl_file_path = model_storage.get_model_path(model_id)

        if not stl_file_path:
            logger.warning(f"Model not found in storage: {model_id}")
            raise HTTPException(status_code=404, detail="Model not found")

        # Verify file still exists
        if not os.path.exists(stl_file_path):
            logger.error(f"Model file missing from filesystem: {stl_file_path}")
            # Clean up the storage reference
            model_storage.delete_model(model_id)
            raise HTTPException(status_code=404, detail="Model not found")

        # Verify file has content
        if os.path.getsize(stl_file_path) == 0:
            logger.error(f"Model file is empty: {stl_file_path}")
            raise HTTPException(status_code=404, detail="Model not found")

        logger.info(
            f"Serving model file: {stl_file_path} ({os.path.getsize(stl_file_path)} bytes)"
        )

        # Track download in analytics
        try:
            await user_manager.track_model_download(model_id)
        except Exception as e:
            logger.warning(f"Failed to track download: {e}")
            # Don't fail the download if tracking fails

        return FileResponse(
            path=stl_file_path,
            filename=f"model_{model_id}.stl",
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=model_{model_id}.stl"
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download_model: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
