"""
Custom exceptions for the Text-to-CAD API
"""
from typing import Optional, Dict, Any


class TextToCADException(Exception):
    """Base exception for all Text-to-CAD exceptions"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)


class BadCADExecutionError(TextToCADException):
    """Raised when BadCAD code execution fails"""
    
    def __init__(self, message: str, code: Optional[str] = None):
        details = {}
        if code:
            details["code"] = code[:200] + "..." if len(code) > 200 else code
        super().__init__(
            message=message,
            status_code=400,
            error_type="BADCAD_EXECUTION_ERROR",
            details=details
        )


class AIGenerationError(TextToCADException):
    """Raised when AI model generation fails"""
    
    def __init__(self, message: str, prompt: Optional[str] = None, original_error: Optional[str] = None):
        details = {}
        if prompt:
            details["prompt"] = prompt
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(
            message=message,
            status_code=503,
            error_type="AI_GENERATION_ERROR",
            details=details
        )


class UserLimitExceededError(TextToCADException):
    """Raised when user exceeds model generation limit"""
    
    def __init__(self, user_id: str, current_count: int, max_count: int):
        super().__init__(
            message=f"Model generation limit reached ({max_count} models max)",
            status_code=403,
            error_type="USER_LIMIT_EXCEEDED",
            details={
                "user_id": user_id,
                "current_count": current_count,
                "max_count": max_count
            }
        )


class ModelNotFoundError(TextToCADException):
    """Raised when a requested model is not found"""
    
    def __init__(self, model_id: str):
        super().__init__(
            message=f"Model not found: {model_id}",
            status_code=404,
            error_type="MODEL_NOT_FOUND",
            details={"model_id": model_id}
        )


class InvalidInputError(TextToCADException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_INPUT",
            details=details
        )


class StorageError(TextToCADException):
    """Raised when file storage operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            status_code=500,
            error_type="STORAGE_ERROR",
            details=details
        )


class ConfigurationError(TextToCADException):
    """Raised when there's a configuration issue"""
    
    def __init__(self, message: str, missing_config: Optional[str] = None):
        details = {}
        if missing_config:
            details["missing_config"] = missing_config
        super().__init__(
            message=message,
            status_code=500,
            error_type="CONFIGURATION_ERROR",
            details=details
        )


class DependencyError(TextToCADException):
    """Raised when a required dependency is not available"""
    
    def __init__(self, dependency: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Required dependency not available: {dependency}",
            status_code=503,
            error_type="DEPENDENCY_ERROR",
            details={"dependency": dependency}
        )


class AuthenticationError(TextToCADException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_type="AUTHENTICATION_ERROR"
        )


class AuthorizationError(TextToCADException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_type="AUTHORIZATION_ERROR"
        )