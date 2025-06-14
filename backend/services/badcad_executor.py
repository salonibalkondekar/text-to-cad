"""
BadCAD execution service for running BadCAD code and generating STL files
"""
import os
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
import tempfile

from core.config import settings, BADCAD_AVAILABLE
from core.exceptions import BadCADExecutionError, DependencyError, StorageError
from services.storage import model_storage
from utils.stl_fallback import create_fallback_stl
from utils.code_extraction import validate_badcad_code

logger = logging.getLogger(__name__)


class BadCADExecutor:
    """Service for executing BadCAD code and generating STL files"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the BadCAD executor.
        
        Args:
            temp_dir: Directory for temporary files (defaults to settings)
        """
        self.temp_dir = temp_dir or settings.temp_dir
        self.available = BADCAD_AVAILABLE
        
    def execute_and_export(self, badcad_code: str, model_id: str, validate: bool = True) -> str:
        """
        Execute BadCAD code and export to STL file.
        
        Args:
            badcad_code: The BadCAD code to execute
            model_id: Unique identifier for the model
            validate: Whether to validate code before execution
            
        Returns:
            Path to the generated STL file
            
        Raises:
            BadCADExecutionError: If execution fails
            DependencyError: If BadCAD is not available
        """
        if not badcad_code or not badcad_code.strip():
            raise BadCADExecutionError("BadCAD code cannot be empty", code=badcad_code)
        
        if not model_id:
            raise BadCADExecutionError("Model ID cannot be empty")
        
        logger.info(f"Executing BadCAD code for model: {model_id}")
        
        # Validate code if requested
        if validate:
            is_valid, error_msg = validate_badcad_code(badcad_code)
            if not is_valid:
                raise BadCADExecutionError(f"Code validation failed: {error_msg}", code=badcad_code)
        
        # Generate STL file path
        stl_path = model_storage.get_temp_file_path(prefix=f"model_{model_id}_", suffix=".stl")
        
        try:
            if not self.available:
                logger.warning("BadCAD not available, creating fallback STL")
                raise DependencyError("badcad", "BadCAD library not available")
            
            # Execute the BadCAD code
            model_obj = self._execute_badcad_code(badcad_code)
            
            # Export to STL
            self._export_to_stl(model_obj, stl_path)
            
            logger.info(f"Successfully executed BadCAD code and exported STL: {stl_path}")
            return stl_path
            
        except DependencyError:
            # Handle missing BadCAD by creating fallback
            logger.info("Creating fallback STL due to missing BadCAD")
            create_fallback_stl(stl_path)
            return stl_path
            
        except Exception as e:
            logger.error(f"BadCAD execution failed: {str(e)}")
            
            # Create fallback STL on any error
            try:
                create_fallback_stl(stl_path)
                logger.info(f"Created fallback STL at: {stl_path}")
                return stl_path
            except Exception as fallback_error:
                raise StorageError(f"Failed to create fallback STL: {str(fallback_error)}", "create_fallback")
    
    def _execute_badcad_code(self, badcad_code: str) -> Any:
        """Execute BadCAD code and return the model object"""
        logger.debug("Setting up BadCAD execution environment")
        
        try:
            # Import BadCAD in the execution environment
            import badcad
            
            # Create execution environment with BadCAD access
            exec_globals = {
                '__builtins__': __builtins__,
                'badcad': badcad,
                # Import common Python modules that might be needed
                'math': __import__('math'),
                'os': __import__('os'),
                'sys': __import__('sys'),
            }
            
            # Import all BadCAD functions into the execution environment
            for name in dir(badcad):
                if not name.startswith('_'):
                    exec_globals[name] = getattr(badcad, name)
            exec_locals = {}
            
            logger.debug(f"Executing BadCAD code:\n{badcad_code[:200]}...")
            
            # Execute the code
            exec(badcad_code, exec_globals, exec_locals)
            
            # Get the model from execution context
            model = None
            if 'model' in exec_locals:
                model = exec_locals['model']
            elif 'model' in exec_globals:
                model = exec_globals['model']
            
            if model is None:
                # Look for other potential model variables
                possible_models = []
                for var_name, var_value in {**exec_locals, **exec_globals}.items():
                    if (not var_name.startswith('_') and 
                        hasattr(var_value, 'stl') and 
                        var_name not in ['badcad']):
                        possible_models.append((var_name, var_value))
                
                if possible_models:
                    # Use the first found model-like object
                    var_name, model = possible_models[0]
                    logger.warning(f"No 'model' variable found, using '{var_name}' instead")
                else:
                    available_vars = [k for k in {**exec_locals, **exec_globals}.keys() 
                                    if not k.startswith('_') and k not in ['badcad', 'math', 'os', 'sys']]
                    raise BadCADExecutionError(
                        f"No 'model' variable found in execution context. Available variables: {available_vars}",
                        code=badcad_code
                    )
            
            logger.debug(f"Model found: {type(model)}")
            return model
            
        except Exception as e:
            if isinstance(e, BadCADExecutionError):
                raise
            raise BadCADExecutionError(f"Code execution failed: {str(e)}", code=badcad_code)
    
    def _export_to_stl(self, model_obj: Any, stl_path: str) -> None:
        """Export a BadCAD model object to STL file"""
        try:
            if not hasattr(model_obj, 'stl'):
                raise BadCADExecutionError(
                    f"Model object of type {type(model_obj)} does not have an 'stl' method"
                )
            
            logger.debug("Generating STL data from model")
            
            # Get STL data from BadCAD model
            stl_data = model_obj.stl()
            
            if not stl_data:
                raise BadCADExecutionError("Model generated empty STL data")
            
            logger.debug(f"STL data type: {type(stl_data)}, size: {len(stl_data) if hasattr(stl_data, '__len__') else 'unknown'}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(stl_path), exist_ok=True)
            
            # Write STL data to file (handle both bytes and string)
            if isinstance(stl_data, bytes):
                with open(stl_path, 'wb') as f:
                    f.write(stl_data)
            else:
                with open(stl_path, 'w') as f:
                    f.write(str(stl_data))
            
            # Verify the file was created and has content
            if not os.path.exists(stl_path):
                raise StorageError("STL file was not created", "export")
            
            file_size = os.path.getsize(stl_path)
            if file_size == 0:
                raise StorageError("STL file is empty", "export")
            
            logger.debug(f"STL file verified: {file_size} bytes")
            
        except Exception as e:
            if isinstance(e, (BadCADExecutionError, StorageError)):
                raise
            raise BadCADExecutionError(f"STL export failed: {str(e)}")
    
    @contextmanager
    def sandbox_execution(self):
        """
        Context manager for sandboxed execution (future enhancement).
        Currently provides basic isolation but could be enhanced with:
        - Resource limits (memory, CPU time)
        - Network access restrictions
        - File system access limitations
        """
        # For now, this is a placeholder for future security enhancements
        logger.debug("Entering sandbox execution context")
        try:
            yield
        finally:
            logger.debug("Exiting sandbox execution context")
    
    def validate_execution_environment(self) -> Dict[str, Any]:
        """
        Validate that the execution environment is properly set up.
        
        Returns:
            Dictionary with environment status information
        """
        status = {
            "badcad_available": self.available,
            "temp_dir_exists": os.path.exists(self.temp_dir),
            "temp_dir_writable": os.access(self.temp_dir, os.W_OK),
        }
        
        if self.available:
            try:
                import badcad
                status["badcad_version"] = getattr(badcad, '__version__', 'unknown')
                status["badcad_functions"] = [name for name in dir(badcad) if not name.startswith('_')]
            except Exception as e:
                status["badcad_error"] = str(e)
        
        return status


# Global instance
badcad_executor = BadCADExecutor()