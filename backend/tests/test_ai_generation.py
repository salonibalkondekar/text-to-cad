"""
Tests for AI generation service
"""
import pytest
from unittest.mock import patch, MagicMock

from services.ai_generation import AICodeGenerator, ai_generator
from core.exceptions import AIGenerationError, ConfigurationError


class TestAICodeGenerator:
    """Test the AICodeGenerator class"""
    
    def test_init_with_defaults(self):
        """Test initialization with default settings"""
        generator = AICodeGenerator()
        assert generator.model_name == "gemini-2.5-flash-preview-04-17"
        assert generator.client is not None or not generator.available
    
    def test_init_with_custom_model(self):
        """Test initialization with custom model"""
        generator = AICodeGenerator(model_name="custom-model")
        assert generator.model_name == "custom-model"
    
    def test_generate_empty_prompt_raises_error(self):
        """Test that empty prompt raises error"""
        generator = AICodeGenerator()
        
        with pytest.raises(AIGenerationError) as exc_info:
            generator.generate_badcad_code("")
        
        assert "empty" in exc_info.value.message.lower()
        assert exc_info.value.status_code == 503
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', False)
    def test_generate_with_unavailable_gemini(self):
        """Test generation when Gemini is unavailable"""
        generator = AICodeGenerator()
        generator.available = False
        
        code = generator.generate_badcad_code("Create a cube")
        
        assert "from badcad import *" in code
        assert "model =" in code
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_gemini_success(self):
        """Test successful generation with Gemini"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """```python
from badcad import *
cube_obj = cube(10, 10, 10)
model = cube_obj
```"""
        mock_client.models.generate_content.return_value = mock_response
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create a cube")
        
        assert "from badcad import *" in code
        assert "cube_obj = cube(10, 10, 10)" in code
        assert "model = cube_obj" in code
        mock_client.models.generate_content.assert_called_once()
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_gemini_empty_response(self):
        """Test handling of empty Gemini response"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create a sphere")
        
        # Should fall back to smart fallback
        assert "from badcad import *" in code
        assert "sphere(" in code or "model =" in code
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_gemini_quota_exhausted(self):
        """Test handling of quota exhausted error"""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("RESOURCE_EXHAUSTED: quota exceeded")
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create a cylinder")
        
        # Should fall back to smart fallback
        assert "from badcad import *" in code
        assert "cylinder(" in code or "model =" in code
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_gemini_permission_denied(self):
        """Test handling of permission denied error"""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("PERMISSION_DENIED: invalid API key")
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create a ring")
        
        # Should fall back to smart fallback
        assert "from badcad import *" in code
        assert "outer - inner" in code or "model =" in code
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_gemini_general_error(self):
        """Test handling of general Gemini error"""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Network error")
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create something")
        
        # Should fall back to smart fallback
        assert "from badcad import *" in code
        assert "model =" in code
    
    @patch('services.ai_generation.GEMINI_AVAILABLE', True)
    def test_generate_with_invalid_code_validation(self):
        """Test handling when generated code fails validation"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """```python
# Invalid code - missing import and model variable
invalid_code = "not badcad code"
```"""
        mock_client.models.generate_content.return_value = mock_response
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create a gear", validate=True)
        
        # Should fall back due to validation failure
        assert "from badcad import *" in code
        assert "model =" in code
    
    def test_generate_without_validation(self):
        """Test generation without code validation"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """```python
# Code without proper structure
some_code = "test"
```"""
        mock_client.models.generate_content.return_value = mock_response
        
        generator = AICodeGenerator()
        generator.client = mock_client
        generator.available = True
        
        code = generator.generate_badcad_code("Create something", validate=False)
        
        assert "some_code = \"test\"" in code
    
    def test_build_full_prompt(self):
        """Test building the full prompt with examples"""
        generator = AICodeGenerator()
        
        full_prompt = generator._build_full_prompt("Create a test object")
        
        assert "You are an expert at generating BadCAD code" in full_prompt
        assert "Create a cross shape" in full_prompt  # From examples
        assert "Create a test object" in full_prompt
        assert "CORE BadCAD API:" in full_prompt
    
    def test_get_system_prompt(self):
        """Test getting the system prompt"""
        generator = AICodeGenerator()
        
        system_prompt = generator._get_system_prompt()
        
        assert "You are an expert at generating BadCAD code" in system_prompt
        assert "square(x, y, center=False)" in system_prompt
        assert "IMPORTANT RULES:" in system_prompt
        assert "from badcad import *" in system_prompt
    
    def test_get_few_shot_examples(self):
        """Test getting few-shot examples"""
        generator = AICodeGenerator()
        
        examples = generator._get_few_shot_examples()
        
        assert len(examples) == 6
        assert all("prompt" in example and "code" in example for example in examples)
        assert any("cross shape" in example["prompt"].lower() for example in examples)
        assert any("from badcad import *" in example["code"] for example in examples)
    
    def test_client_not_initialized_error(self):
        """Test error when client is not initialized"""
        generator = AICodeGenerator()
        generator.client = None
        generator.available = True
        
        with pytest.raises(ConfigurationError):
            generator._generate_with_gemini("test prompt")


class TestGlobalAIGenerator:
    """Test the global ai_generator instance"""
    
    def test_global_instance_exists(self):
        """Test that global instance is properly initialized"""
        assert ai_generator is not None
        assert isinstance(ai_generator, AICodeGenerator)
    
    def test_global_instance_functional(self):
        """Test that global instance can generate code"""
        with patch.object(ai_generator, 'available', False):
            code = ai_generator.generate_badcad_code("Create a simple box")
            
            assert "from badcad import *" in code
            assert "model =" in code


class TestPromptBuilding:
    """Test prompt building functionality"""
    
    def test_prompt_contains_all_examples(self):
        """Test that full prompt contains all few-shot examples"""
        generator = AICodeGenerator()
        examples = generator._get_few_shot_examples()
        
        full_prompt = generator._build_full_prompt("test")
        
        for example in examples:
            assert example["prompt"] in full_prompt
            assert "from badcad import *" in full_prompt
    
    def test_prompt_structure(self):
        """Test the structure of the built prompt"""
        generator = AICodeGenerator()
        
        full_prompt = generator._build_full_prompt("Create a test shape")
        
        # Should contain system prompt
        assert "You are an expert" in full_prompt
        
        # Should contain examples section
        assert "Here are some examples" in full_prompt
        
        # Should contain user prompt
        assert "Create a test shape" in full_prompt
        
        # Should end with code request
        assert "BadCAD Code:" in full_prompt


class TestErrorHandling:
    """Test error handling in AI generation"""
    
    def test_specific_error_types(self):
        """Test handling of specific error types"""
        generator = AICodeGenerator()
        
        # Test quota exhausted
        with patch.object(generator, '_generate_with_gemini') as mock_gen:
            mock_gen.side_effect = Exception("RESOURCE_EXHAUSTED: quota limit")
            code = generator.generate_badcad_code("test")
            assert "from badcad import *" in code
        
        # Test permission denied
        with patch.object(generator, '_generate_with_gemini') as mock_gen:
            mock_gen.side_effect = Exception("PERMISSION_DENIED: invalid key")
            code = generator.generate_badcad_code("test")
            assert "from badcad import *" in code
        
        # Test general error
        with patch.object(generator, '_generate_with_gemini') as mock_gen:
            mock_gen.side_effect = Exception("Some other error")
            code = generator.generate_badcad_code("test")
            assert "from badcad import *" in code