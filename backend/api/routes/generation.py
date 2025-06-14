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
async def generate_model(request: PromptRequest, http_request: Request):
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
            # Check if user can generate more models
            try:
                await user_manager.check_user_limit(request.user_id)
            except UserLimitExceededError:
                raise HTTPException(
                    status_code=403, 
                    detail="Model generation limit reached (10 models max)"
                )
        
        # Track timing
        generation_start = time.time()
        
        # Generate BadCAD code using AI
        ai_start = time.time()
        try:
            badcad_code = ai_generator.generate_badcad_code(request.prompt)
            generation_status = GenerationStatus.AI_GENERATED
            logger.info("Successfully generated code using AI")
        except (AIGenerationError, DependencyError) as ai_error:
            logger.warning(f"AI generation failed: {ai_error}, using fallback")
            # ai_generator.generate_badcad_code already handles fallbacks internally
            badcad_code = ai_generator._generate_fallback_code(request.prompt)
            generation_status = GenerationStatus.FALLBACK_GENERATED
        ai_time_ms = int((time.time() - ai_start) * 1000)
        
        # Execute BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        
        execution_start = time.time()
        try:
            stl_file_path = badcad_executor.execute_and_export(badcad_code, model_id)
            logger.info(f"Successfully executed BadCAD code, STL at: {stl_file_path}")
        except Exception as exec_error:
            logger.error(f"BadCAD execution failed: {exec_error}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to execute BadCAD code and generate STL"
            )
        execution_time_ms = int((time.time() - execution_start) * 1000)
        total_time_ms = int((time.time() - generation_start) * 1000)
        
        # Store the model file reference
        model_storage.store_model(model_id, stl_file_path)
        
        # Get file size for analytics
        stl_file_size = 0
        try:
            import os
            stl_file_size = os.path.getsize(stl_file_path)
        except:
            pass
        
        # Track generation and increment count if authenticated
        if request.user_id:
            try:
                # Get session cookie from request (if available)
                session_cookie = None
                cookie_header = http_request.headers.get("cookie", "")
                if "session_id=" in cookie_header:
                    # Extract session_id value from cookie header
                    for cookie in cookie_header.split(";"):
                        cookie = cookie.strip()
                        if cookie.startswith("session_id="):
                            session_cookie = cookie.split("=", 1)[1]
                            break
                
                if session_cookie:
                    # Increment model count
                    await user_manager.increment_model_count(request.user_id, session_cookie)
                    
                    # Store comprehensive model data in analytics
                    await user_manager.store_generated_model(
                        session_cookie=session_cookie,
                        model_id=model_id,
                        prompt=request.prompt,
                        generated_code=badcad_code,
                        stl_file_path=stl_file_path,
                        stl_file_size=stl_file_size,
                        generation_time_ms=total_time_ms,
                        ai_generation_time_ms=ai_time_ms,
                        execution_time_ms=execution_time_ms,
                        success=True
                    )
                    
                    # Track the generation event with additional metadata
                    await user_manager.track_generation(
                        session_cookie=session_cookie,
                        prompt=request.prompt,
                        success=True,
                        generation_time=total_time_ms / 1000.0,
                        model_id=model_id,
                        stl_file_path=stl_file_path,
                        generated_code=badcad_code
                    )
            except Exception as e:
                logger.warning(f"Failed to track generation: {e}")
                # Don't fail the request if tracking fails
        
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
async def execute_badcad_code(request: BadCADCodeRequest, http_request: Request):
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
            # Check if user can generate more models
            try:
                await user_manager.check_user_limit(request.user_id)
            except UserLimitExceededError:
                raise HTTPException(
                    status_code=403, 
                    detail="Model generation limit reached (10 models max)"
                )
        
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
        
        # Track execution and increment count if authenticated
        if request.user_id:
            try:
                # Get session cookie from request (if available)
                session_cookie = http_request.headers.get("cookie", "").split("session_id=")[-1].split(";")[0] if "session_id=" in http_request.headers.get("cookie", "") else None
                
                if session_cookie:
                    # Increment model count
                    await user_manager.increment_model_count(request.user_id, session_cookie)
                    
                    # Track the execution event
                    await user_manager.track_generation(
                        session_cookie=session_cookie,
                        prompt=f"[BadCAD Code]: {request.code[:100]}...",
                        success=True,
                        generation_time=None
                    )
            except Exception as e:
                logger.warning(f"Failed to track execution: {e}")
                # Don't fail the request if tracking fails
        
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