"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PromptType(str, Enum):
    """Types of prompts stored in the system"""

    GENERATE = "generate"
    EXECUTE_CODE = "execute_code"


class GenerationStatus(str, Enum):
    """Status of model generation"""

    AI_GENERATED = "ai_generated"
    FALLBACK_GENERATED = "fallback_generated"
    USER_PROVIDED = "user_provided"


# Request Models
class PromptRequest(BaseModel):
    """Request for generating a model from natural language prompt"""

    prompt: str = Field(
        ..., min_length=1, description="Natural language description of the 3D model"
    )
    user_id: Optional[str] = Field(None, description="Unique identifier for the user")


class BadCADCodeRequest(BaseModel):
    """Request for executing user-provided BadCAD code"""

    code: str = Field(..., min_length=1, description="BadCAD code to execute")
    user_id: Optional[str] = Field(None, description="Unique identifier for the user")


class UserInfoRequest(BaseModel):
    """Request for user information registration/update"""

    user_id: str = Field(..., description="Unique identifier for the user")
    email: str = Field(
        ..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="User email address"
    )
    name: str = Field(..., min_length=1, description="User's name")


class UserCountRequest(BaseModel):
    """Request for incrementing user's model count"""

    user_id: str = Field(..., description="Unique identifier for the user")


# Response Models
class GenerateResponse(BaseModel):
    """Response from model generation endpoint"""

    success: bool = Field(..., description="Whether the generation was successful")
    model_id: str = Field(..., description="Unique identifier for the generated model")
    badcad_code: str = Field(..., description="BadCAD code used to generate the model")
    message: str = Field(..., description="Human-readable status message")
    generation_status: Optional[GenerationStatus] = Field(
        None, description="How the model was generated"
    )


class ExecuteResponse(BaseModel):
    """Response from BadCAD code execution endpoint"""

    success: bool = Field(..., description="Whether the execution was successful")
    model_id: str = Field(..., description="Unique identifier for the generated model")
    message: str = Field(..., description="Human-readable status message")


class UserInfoResponse(BaseModel):
    """Response with user information"""

    success: bool = Field(..., description="Whether the request was successful")
    user_id: str = Field(..., description="Unique identifier for the user")
    model_count: int = Field(
        ..., ge=0, description="Number of models generated by the user"
    )
    max_models: int = Field(..., gt=0, description="Maximum number of models allowed")


class UserCountResponse(BaseModel):
    """Response with updated user model count"""

    success: bool = Field(..., description="Whether the increment was successful")
    model_count: int = Field(..., ge=0, description="Updated model count for the user")


# Internal Models
class UserPrompt(BaseModel):
    """A single prompt from a user"""

    prompt: str = Field(..., description="The prompt text or code")
    type: PromptType = Field(..., description="Type of prompt")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the prompt was created"
    )


class UserData(BaseModel):
    """Complete user data stored in the system"""

    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User's name")
    prompts: List[UserPrompt] = Field(
        default_factory=list, description="All prompts from this user"
    )
    model_count: int = Field(default=0, ge=0, description="Number of models generated")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the user was first seen"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )


# Admin Response Models
class UserSummary(BaseModel):
    """Summary of a single user for admin endpoint"""

    user_id: str
    email: str
    name: Optional[str]
    model_count: int
    total_prompts: int
    created_at: str
    last_activity: str
    recent_prompts: List[dict]


class AdminSummaryResponse(BaseModel):
    """Response from admin endpoint with all user data"""

    total_users: int
    total_prompts: int
    total_models_generated: int
    users: List[UserSummary]


# Error Response Models
class ErrorDetail(BaseModel):
    """Detailed error information"""

    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    details: Optional[dict] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = Field(default=False)
    error: ErrorDetail
    request_id: Optional[str] = Field(None, description="Request tracking ID")
