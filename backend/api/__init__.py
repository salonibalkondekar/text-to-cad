"""
API package initialization

This module sets up the FastAPI router configuration and dependency injection
for the modular API structure.
"""

from fastapi import FastAPI
from .routes import generation, download, user, admin
from .dependencies import (
    get_ai_generator,
    get_badcad_executor,
    get_user_manager,
    get_model_storage,
)


def create_api_router():
    """
    Create and configure the main API router with all sub-routes.

    Returns:
        FastAPI app instance with all routes configured
    """
    app = FastAPI(
        title="Text-to-CAD API",
        description="Generate 3D CAD models from text descriptions",
        version="2.0.0",
    )

    # Include all route modules
    app.include_router(generation.router)
    app.include_router(download.router)
    app.include_router(user.router)
    app.include_router(admin.router)

    return app


__all__ = [
    "create_api_router",
    "get_ai_generator",
    "get_badcad_executor",
    "get_user_manager",
    "get_model_storage",
]
