"""
Tests for BadCAD executor service
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open

from services.badcad_executor import BadCADExecutor, badcad_executor
from core.exceptions import BadCADExecutionError, DependencyError, StorageError


class TestBadCADExecutor:
    """Test the BadCADExecutor class"""
    
    def test_init_with_defaults(self):
        """Test initialization with default settings"""
        executor = BadCADExecutor()
        assert executor.temp_dir is not None
        assert isinstance(executor.available, bool)
    
    def test_init_with_custom_temp_dir(self):
        """Test initialization with custom temp directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = BadCADExecutor(temp_dir=temp_dir)
            assert executor.temp_dir == temp_dir
    
    def test_execute_empty_code_raises_error(self):
        """Test that empty code raises error"""
        executor = BadCADExecutor()
        
        with pytest.raises(BadCADExecutionError) as exc_info:
            executor.execute_and_export("", "test_model")
        
        assert "empty" in exc_info.value.message.lower()
    
    def test_execute_empty_model_id_raises_error(self):
        """Test that empty model ID raises error"""
        executor = BadCADExecutor()
        
        with pytest.raises(BadCADExecutionError) as exc_info:
            executor.execute_and_export("valid code", "")
        
        assert "model id" in exc_info.value.message.lower()
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', False)
    def test_execute_with_unavailable_badcad(self):
        """Test execution when BadCAD is unavailable"""
        executor = BadCADExecutor()
        executor.available = False
        
        with patch('services.badcad_executor.create_fallback_stl') as mock_fallback:
            stl_path = executor.execute_and_export("from badcad import *\nmodel = cube(10,10,10)", "test_model")
            
            mock_fallback.assert_called_once()
            assert stl_path is not None
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_execute_with_valid_code(self):
        """Test execution with valid BadCAD code"""
        # Mock BadCAD module and model object
        mock_model = MagicMock()
        mock_model.stl.return_value = "STL content here"
        
        # Mock the execution environment
        with patch('builtins.exec') as mock_exec:
            def side_effect(code, globals_dict, locals_dict=None):
                if locals_dict is not None:
                    locals_dict['model'] = mock_model
                else:
                    globals_dict['model'] = mock_model
            
            mock_exec.side_effect = side_effect
            
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=100):
                        with patch('os.makedirs'):
                            executor = BadCADExecutor()
                            executor.available = True
                            
                            stl_path = executor.execute_and_export(
                                "from badcad import *\nmodel = cube(10,10,10)", 
                                "test_model"
                            )
                            
                            assert stl_path is not None
                            mock_model.stl.assert_called_once()
                            mock_file.assert_called()
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_execute_with_invalid_code_validation(self):
        """Test execution with code that fails validation"""
        executor = BadCADExecutor()
        executor.available = True
        
        with pytest.raises(BadCADExecutionError) as exc_info:
            executor.execute_and_export("invalid python code =", "test_model", validate=True)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_execute_without_validation(self):
        """Test execution without code validation"""
        mock_model = MagicMock()
        mock_model.stl.return_value = "STL content"
        
        with patch('builtins.exec') as mock_exec:
            def side_effect(code, globals_dict, locals_dict=None):
                if locals_dict is not None:
                    locals_dict['model'] = mock_model
                else:
                    globals_dict['model'] = mock_model
            
            mock_exec.side_effect = side_effect
            
            with patch('builtins.open', mock_open()):
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=100):
                        with patch('os.makedirs'):
                            executor = BadCADExecutor()
                            executor.available = True
                            
                            # This would fail validation but we're skipping it
                            stl_path = executor.execute_and_export(
                                "invalid = syntax", 
                                "test_model", 
                                validate=False
                            )
                            
                            assert stl_path is not None
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_execute_with_no_model_variable(self):
        """Test execution when no model variable is found"""
        with patch('builtins.exec') as mock_exec:
            # Exec doesn't set any model variable
            mock_exec.return_value = None
            
            with patch('services.badcad_executor.create_fallback_stl') as mock_fallback:
                executor = BadCADExecutor()
                executor.available = True
                
                stl_path = executor.execute_and_export(
                    "from badcad import *\nother_var = cube(10,10,10)", 
                    "test_model",
                    validate=False  # Skip validation for this test
                )
                
                # Should fall back due to missing model variable
                mock_fallback.assert_called_once()
                assert stl_path is not None
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_execute_with_alternative_model_variable(self):
        """Test execution when model is in different variable"""
        mock_model = MagicMock()
        mock_model.stl.return_value = "STL content"
        
        with patch('builtins.exec') as mock_exec:
            def side_effect(code, globals_dict, locals_dict=None):
                # Put model in different variable name
                target_dict = locals_dict if locals_dict is not None else globals_dict
                target_dict['my_shape'] = mock_model
            
            mock_exec.side_effect = side_effect
            
            with patch('builtins.open', mock_open()):
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=100):
                        with patch('os.makedirs'):
                            executor = BadCADExecutor()
                            executor.available = True
                            
                            stl_path = executor.execute_and_export(
                                "from badcad import *\nmy_shape = cube(10,10,10)", 
                                "test_model",
                                validate=False  # Skip validation for this test
                            )
                            
                            assert stl_path is not None
                            mock_model.stl.assert_called_once()
    
    def test_execute_badcad_code_with_execution_error(self):
        """Test handling of code execution errors"""
        executor = BadCADExecutor()
        executor.available = True
        
        with patch('builtins.exec', side_effect=SyntaxError("Invalid syntax")):
            with pytest.raises(BadCADExecutionError) as exc_info:
                executor._execute_badcad_code("invalid code")
            
            assert "execution failed" in exc_info.value.message.lower()
    
    def test_export_to_stl_with_model_without_stl_method(self):
        """Test STL export with model that doesn't have stl method"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        del mock_model.stl  # Remove stl method
        
        with pytest.raises(BadCADExecutionError) as exc_info:
            executor._export_to_stl(mock_model, "/tmp/test.stl")
        
        assert "does not have an 'stl' method" in exc_info.value.message
    
    def test_export_to_stl_with_empty_stl_data(self):
        """Test STL export when model returns empty STL data"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        mock_model.stl.return_value = ""
        
        with pytest.raises(BadCADExecutionError) as exc_info:
            executor._export_to_stl(mock_model, "/tmp/test.stl")
        
        assert "empty STL data" in exc_info.value.message
    
    def test_export_to_stl_bytes_data(self):
        """Test STL export with bytes data"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        mock_model.stl.return_value = b"binary STL data"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=100):
                    with patch('os.makedirs'):
                        executor._export_to_stl(mock_model, "/tmp/test.stl")
                        
                        # Should open in binary mode for bytes
                        mock_file.assert_called_with("/tmp/test.stl", 'wb')
    
    def test_export_to_stl_string_data(self):
        """Test STL export with string data"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        mock_model.stl.return_value = "text STL data"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=100):
                    with patch('os.makedirs'):
                        executor._export_to_stl(mock_model, "/tmp/test.stl")
                        
                        # Should open in text mode for strings
                        mock_file.assert_called_with("/tmp/test.stl", 'w')
    
    def test_export_to_stl_file_not_created(self):
        """Test STL export when file is not created"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        mock_model.stl.return_value = "STL data"
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=False):  # File not created
                with patch('os.makedirs'):
                    with pytest.raises(StorageError) as exc_info:
                        executor._export_to_stl(mock_model, "/tmp/test.stl")
                    
                    assert "was not created" in exc_info.value.message
    
    def test_export_to_stl_empty_file(self):
        """Test STL export when file is empty"""
        executor = BadCADExecutor()
        
        mock_model = MagicMock()
        mock_model.stl.return_value = "STL data"
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=0):  # Empty file
                    with patch('os.makedirs'):
                        with pytest.raises(StorageError) as exc_info:
                            executor._export_to_stl(mock_model, "/tmp/test.stl")
                        
                        assert "is empty" in exc_info.value.message
    
    def test_sandbox_execution_context_manager(self):
        """Test sandbox execution context manager"""
        executor = BadCADExecutor()
        
        # Should work as a context manager
        with executor.sandbox_execution():
            pass  # Context manager should work without errors
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', True)
    def test_validate_execution_environment_with_badcad(self):
        """Test environment validation when BadCAD is available"""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = BadCADExecutor(temp_dir=temp_dir)
            executor.available = True
            
            with patch('importlib.import_module') as mock_import:
                mock_badcad = MagicMock()
                mock_badcad.__version__ = "1.0.0"
                mock_import.return_value = mock_badcad
                
                status = executor.validate_execution_environment()
                
                assert status["badcad_available"] is True
                assert status["temp_dir_exists"] is True
                assert status["temp_dir_writable"] is True
    
    @patch('services.badcad_executor.BADCAD_AVAILABLE', False)
    def test_validate_execution_environment_without_badcad(self):
        """Test environment validation when BadCAD is not available"""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = BadCADExecutor(temp_dir=temp_dir)
            executor.available = False
            
            status = executor.validate_execution_environment()
            
            assert status["badcad_available"] is False
            assert status["temp_dir_exists"] is True
            assert status["temp_dir_writable"] is True


class TestGlobalBadCADExecutor:
    """Test the global badcad_executor instance"""
    
    def test_global_instance_exists(self):
        """Test that global instance is properly initialized"""
        assert badcad_executor is not None
        assert isinstance(badcad_executor, BadCADExecutor)
    
    def test_global_instance_functional(self):
        """Test that global instance can execute code"""
        with patch.object(badcad_executor, 'available', False):
            with patch('services.badcad_executor.create_fallback_stl') as mock_fallback:
                stl_path = badcad_executor.execute_and_export(
                    "from badcad import *\nmodel = cube(10,10,10)", 
                    "test_global"
                )
                
                mock_fallback.assert_called_once()
                assert stl_path is not None


class TestCodeExecution:
    """Test actual code execution scenarios"""
    
    def test_execute_simple_cube_code(self):
        """Test executing simple cube creation code"""
        executor = BadCADExecutor()
        
        # Mock a successful execution
        mock_model = MagicMock()
        mock_model.stl.return_value = "solid cube\n...\nendsolid cube"
        
        with patch('builtins.exec') as mock_exec:
            def side_effect(code, globals_dict, locals_dict=None):
                target_dict = locals_dict if locals_dict is not None else globals_dict
                target_dict['model'] = mock_model
            
            mock_exec.side_effect = side_effect
            
            with patch('builtins.open', mock_open()):
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=100):
                        with patch('os.makedirs'):
                            executor.available = True
                            
                            code = """
from badcad import *
cube_obj = cube(10, 10, 10, center=True)
model = cube_obj
"""
                            
                            stl_path = executor.execute_and_export(code, "cube_test")
                            
                            assert stl_path is not None
                            mock_exec.assert_called_once()
                            mock_model.stl.assert_called_once()