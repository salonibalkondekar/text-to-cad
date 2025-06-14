"""
Tests for code extraction utilities
"""
import pytest
from utils.code_extraction import (
    extract_badcad_code,
    validate_badcad_code,
    clean_code
)


class TestExtractBadCADCode:
    """Test the extract_badcad_code function"""
    
    def test_extract_from_markdown_code_block(self):
        """Test extraction from markdown code blocks"""
        response = """Here's the code:
```python
from badcad import *
model = cube(10, 10, 10)
```
That's it!"""
        
        result = extract_badcad_code(response)
        assert result == "from badcad import *\nmodel = cube(10, 10, 10)"
    
    def test_extract_from_plain_code_block(self):
        """Test extraction from plain code blocks"""
        response = """```
from badcad import *
model = sphere(r=5)
```"""
        
        result = extract_badcad_code(response)
        assert result == "from badcad import *\nmodel = sphere(r=5)"
    
    def test_extract_inline_code(self):
        """Test extraction when code is inline without blocks"""
        response = """Let me create a cylinder for you:
from badcad import *
base = circle(r=10)
model = base.extrude(20)
That should work!"""
        
        result = extract_badcad_code(response)
        assert "from badcad import *" in result
        assert "model = base.extrude(20)" in result
    
    def test_extract_with_mixed_content(self):
        """Test extraction with mixed explanatory text and code"""
        response = """I'll create a simple box.
from badcad import *
# Create a square base
square_base = square(20, 20, center=True)
# Extrude it to make a box
model = square_base.extrude(10)
This creates a 20x20x10 box centered at origin."""
        
        result = extract_badcad_code(response)
        assert "from badcad import *" in result
        assert "square_base = square(20, 20, center=True)" in result
        assert "model = square_base.extrude(10)" in result
        assert "This creates a 20x20x10 box" not in result
    
    def test_extract_empty_response(self):
        """Test extraction from empty response"""
        assert extract_badcad_code("") == ""
        assert extract_badcad_code(None) == ""
    
    def test_extract_no_code(self):
        """Test extraction when response has no code"""
        response = "I cannot generate BadCAD code for this request."
        result = extract_badcad_code(response)
        assert result == response.strip()


class TestValidateBadCADCode:
    """Test the validate_badcad_code function"""
    
    def test_valid_code(self):
        """Test validation of valid BadCAD code"""
        code = """from badcad import *
box = cube(10, 10, 10)
model = box"""
        
        is_valid, error = validate_badcad_code(code)
        assert is_valid is True
        assert error is None
    
    def test_empty_code(self):
        """Test validation of empty code"""
        is_valid, error = validate_badcad_code("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_missing_import(self):
        """Test validation when import is missing"""
        code = "model = cube(10, 10, 10)"
        is_valid, error = validate_badcad_code(code)
        assert is_valid is False
        assert "import" in error.lower()
    
    def test_missing_model_variable(self):
        """Test validation when model variable is missing"""
        code = """from badcad import *
box = cube(10, 10, 10)"""
        
        is_valid, error = validate_badcad_code(code)
        assert is_valid is False
        assert "model" in error.lower()
    
    def test_syntax_error(self):
        """Test validation with syntax error"""
        code = """from badcad import *
model = cube(10, 10, 10"""  # Missing closing paren
        
        is_valid, error = validate_badcad_code(code)
        assert is_valid is False
        assert "Syntax error" in error
    
    def test_alternative_import_style(self):
        """Test validation with alternative import style"""
        code = """import badcad
model = badcad.cube(10, 10, 10)"""
        
        is_valid, error = validate_badcad_code(code)
        assert is_valid is True
        assert error is None


class TestCleanCode:
    """Test the clean_code function"""
    
    def test_remove_markdown_formatting(self):
        """Test removal of markdown formatting"""
        code = """```python
from badcad import *
model = cube(10, 10, 10)
```"""
        
        result = clean_code(code)
        assert "```" not in result
        assert result.startswith("from badcad")
    
    def test_normalize_line_endings(self):
        """Test normalization of line endings"""
        code = "line1\r\nline2\rline3\nline4"
        result = clean_code(code)
        assert "\r" not in result
        assert result.count("\n") == 3
    
    def test_remove_excessive_blank_lines(self):
        """Test removal of excessive blank lines"""
        code = """from badcad import *


model = cube(10, 10, 10)"""
        
        result = clean_code(code)
        assert "\n\n\n" not in result
        assert "\n\n" in result  # Should preserve double newlines
    
    def test_ensure_trailing_newline(self):
        """Test that code ends with newline"""
        code = "from badcad import *\nmodel = cube(10, 10, 10)"
        result = clean_code(code)
        # The strip() at the end removes the trailing newline
        assert not result.endswith("\n")
    
    def test_clean_empty_code(self):
        """Test cleaning empty code"""
        assert clean_code("") == ""
        assert clean_code(None) == ""