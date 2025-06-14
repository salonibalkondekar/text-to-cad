"""
API routes for model generation functionality
"""
import uuid
import logging
import time
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from core.models import (
    PromptRequest, BadCADCodeRequest, GenerateResponse, ExecuteResponse, 
    GenerationStatus
)
from core.exceptions import (
    AIGenerationError, BadCADExecutionError, UserLimitExceededError,
    DependencyError, StorageError
)
from services.ai_generation import ai_generator
from services.badcad_executor import badcad_executor
from services.storage import model_storage
from services.user_management import user_manager
from services.analytics_client import analytics_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_model(request: PromptRequest):
    """
    Generate a 3D model from a natural language prompt.
    
    Uses AI to convert the prompt into BadCAD code, then executes the code
    to generate an STL file for download.
    """
    try:
        # Validate prompt
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        logger.info(f"Generating model for prompt: '{request.prompt[:100]}...'")
        
        # Check user limits if authenticated
        if request.user_id:
            # Create user if doesn't exist (for backward compatibility)
            user_data = user_manager.get_user(request.user_id)
            if not user_data:
                logger.info(f"Creating new user for generation: {request.user_id}")
                user_manager.create_or_update_user(
                    user_id=request.user_id,
                    email=f"{request.user_id}@generated.local",  # Default email
                    name=f"User {request.user_id}"  # Default name
                )
            
            if not user_manager.check_user_can_generate(request.user_id):
                raise HTTPException(
                    status_code=403, 
                    detail="Model generation limit reached (10 models max)"
                )
        
        # Record the prompt
        if request.user_id:
            user_manager.record_user_prompt(request.user_id, request.prompt, "generate")
        
        # Generate BadCAD code using AI
        try:
            badcad_code = ai_generator.generate_badcad_code(request.prompt)
            generation_status = GenerationStatus.AI_GENERATED
            logger.info("Successfully generated code using AI")
        except (AIGenerationError, DependencyError) as ai_error:
            logger.warning(f"AI generation failed: {ai_error}, using fallback")
            # ai_generator.generate_badcad_code already handles fallbacks internally
            badcad_code = ai_generator._generate_fallback_code(request.prompt)
            generation_status = GenerationStatus.FALLBACK_GENERATED
        
        # Execute BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        
        try:
            stl_file_path = badcad_executor.execute_and_export(badcad_code, model_id)
            logger.info(f"Successfully executed BadCAD code, STL at: {stl_file_path}")
        except Exception as exec_error:
            logger.error(f"BadCAD execution failed: {exec_error}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to execute BadCAD code and generate STL"
            )
        
        # Store the model file reference
        model_storage.store_model(model_id, stl_file_path)
        
        # Increment user model count if authenticated
        if request.user_id:
            try:
                user_manager.increment_user_model_count(request.user_id)
            except UserLimitExceededError:
                # This shouldn't happen as we checked earlier, but handle it
                raise HTTPException(status_code=403, detail="Model generation limit exceeded")
        
        # Create response message
        if generation_status == GenerationStatus.AI_GENERATED:
            message = f'Generated model for: "{request.prompt}"'
        else:
            message = f'Generated fallback model for: "{request.prompt}" (AI service temporarily unavailable)'
        
        return GenerateResponse(
            success=True,
            model_id=model_id,
            badcad_code=badcad_code,
            message=message,
            generation_status=generation_status
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_model: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/execute", response_model=ExecuteResponse)
async def execute_badcad_code(request: BadCADCodeRequest):
    """
    Execute user-provided BadCAD code to generate an STL file.
    
    Allows users to provide their own BadCAD code for execution,
    bypassing the AI generation step.
    """
    try:
        # Validate code
        if not request.code or not request.code.strip():
            raise HTTPException(status_code=400, detail="No code provided")
        
        logger.info(f"Executing user-provided BadCAD code (user: {request.user_id})")
        
        # Check user limits if authenticated
        if request.user_id:
            # Create user if doesn't exist (for backward compatibility)
            user_data = user_manager.get_user(request.user_id)
            if not user_data:
                logger.info(f"Creating new user for execution: {request.user_id}")
                user_manager.create_or_update_user(
                    user_id=request.user_id,
                    email=f"{request.user_id}@generated.local",  # Default email
                    name=f"User {request.user_id}"  # Default name
                )
            
            if not user_manager.check_user_can_generate(request.user_id):
                raise HTTPException(
                    status_code=403, 
                    detail="Model generation limit reached (10 models max)"
                )
        
        # Record the code execution
        if request.user_id:
            user_manager.record_user_prompt(request.user_id, request.code, "execute_code")
        
        # Execute the user-provided BadCAD code
        model_id = str(uuid.uuid4())
        
        try:
            stl_file_path = badcad_executor.execute_and_export(
                request.code, 
                model_id, 
                validate=True  # Validate user-provided code
            )
            logger.info(f"Successfully executed user code, STL at: {stl_file_path}")
        except BadCADExecutionError as exec_error:
            logger.error(f"BadCAD execution failed: {exec_error}")
            raise HTTPException(
                status_code=400, 
                detail=f"BadCAD code execution failed: {exec_error.message}"
            )
        except Exception as exec_error:
            logger.error(f"Unexpected execution error: {exec_error}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to execute BadCAD code"
            )
        
        # Store the model file reference
        model_storage.store_model(model_id, stl_file_path)
        
        # Increment user model count if authenticated
        if request.user_id:
            try:
                user_manager.increment_user_model_count(request.user_id)
            except UserLimitExceededError:
                raise HTTPException(status_code=403, detail="Model generation limit exceeded")
        
        return ExecuteResponse(
            success=True,
            model_id=model_id,
            message="BadCAD code executed successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_badcad_code: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")