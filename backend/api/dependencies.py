"""
Dependency injection for API routes

This module provides dependency injection functions for FastAPI routes,
ensuring consistent service instances across the application.
"""

from typing import Annotated
from fastapi import Depends

from services.ai_generation import ai_generator
from services.badcad_executor import badcad_executor
from services.user_management import user_manager
from services.storage import model_storage


def get_ai_generator():
    """
    Dependency to get the AI code generator service.

    Returns:
        AICodeGenerator: The singleton AI generator instance
    """
    return ai_generator


def get_badcad_executor():
    """
    Dependency to get the BadCAD executor service.

    Returns:
        BadCADExecutor: The singleton BadCAD executor instance
    """
    return badcad_executor


def get_user_manager():
    """
    Dependency to get the user management service.

    Returns:
        UserManager: The singleton user manager instance
    """
    return user_manager


def get_model_storage():
    """
    Dependency to get the model storage service.

    Returns:
        ModelStorage: The singleton model storage instance
    """
    return model_storage


# Type annotations for dependency injection
AIGeneratorDep = Annotated[type(ai_generator), Depends(get_ai_generator)]
BadCADExecutorDep = Annotated[type(badcad_executor), Depends(get_badcad_executor)]
UserManagerDep = Annotated[type(user_manager), Depends(get_user_manager)]
ModelStorageDep = Annotated[type(model_storage), Depends(get_model_storage)]
