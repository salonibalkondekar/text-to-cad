"""
Tests for STL fallback utilities
"""
import os
import tempfile
import pytest
from utils.stl_fallback import (
    create_fallback_stl,
    generate_smart_fallback_badcad_code,
    generate_hardcoded_badcad_code
)


class TestCreateFallbackSTL:
    """Test the create_fallback_stl function"""
    
    def test_create_stl_file(self):
        """Test creating a fallback STL file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as f:
            temp_path = f.name
        
        try:
            create_fallback_stl(temp_path)
            
            # Verify file exists
            assert os.path.exists(temp_path)
            
            # Verify file has content
            assert os.path.getsize(temp_path) > 0
            
            # Verify STL format
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content.startswith("solid cube")
                assert "facet normal" in content
                assert "vertex" in content
                assert content.endswith("endsolid cube")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_create_stl_with_directory_creation(self):
        """Test creating STL file with non-existent directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            stl_path = os.path.join(temp_dir, "subdir", "test.stl")
            
            create_fallback_stl(stl_path)
            
            assert os.path.exists(stl_path)
            assert os.path.getsize(stl_path) > 0


class TestGenerateSmartFallbackBadCADCode:
    """Test the generate_smart_fallback_badcad_code function"""
    
    def test_cone_keywords(self):
        """Test generation for cone-related keywords"""
        for keyword in ['cone', 'triangle', 'pyramid']:
            code = generate_smart_fallback_badcad_code(f"create a {keyword}")
            assert "from badcad import *" in code
            assert "extrude_to" in code
            assert "circle" in code
            assert "model =" in code
    
    def test_sphere_keywords(self):
        """Test generation for sphere-related keywords"""
        for keyword in ['sphere', 'ball', 'round object', 'orb']:
            code = generate_smart_fallback_badcad_code(f"make a {keyword}")
            assert "from badcad import *" in code
            assert "sphere(" in code
            assert "model =" in code
    
    def test_cylinder_keywords(self):
        """Test generation for cylinder-related keywords"""
        for keyword in ['cylinder', 'tube', 'pipe', 'rod']:
            code = generate_smart_fallback_badcad_code(f"design a {keyword}")
            assert "from badcad import *" in code
            assert "cylinder(" in code
            assert "model =" in code
    
    def test_ring_keywords(self):
        """Test generation for ring-related keywords"""
        for keyword in ['ring', 'washer', 'donut', 'torus']:
            code = generate_smart_fallback_badcad_code(f"generate a {keyword}")
            assert "from badcad import *" in code
            assert "outer - inner" in code
            assert "circle" in code
            assert "model =" in code
    
    def test_gear_keywords(self):
        """Test generation for gear-related keywords"""
        for keyword in ['gear', 'cog', 'sprocket']:
            code = generate_smart_fallback_badcad_code(f"build a {keyword} with teeth")
            assert "from badcad import *" in code
            assert "import math" in code
            assert "for i in range" in code
            assert "model =" in code
    
    def test_star_keywords(self):
        """Test generation for star-related keywords"""
        code = generate_smart_fallback_badcad_code("create a star shape")
        assert "from badcad import *" in code
        assert "import math" in code
        assert "polygon" in code
        assert "model =" in code
    
    def test_hexagon_keywords(self):
        """Test generation for hexagon-related keywords"""
        for keyword in ['hexagon', 'hex nut', 'bolt head']:
            code = generate_smart_fallback_badcad_code(f"make a {keyword}")
            assert "from badcad import *" in code
            assert "fn=6" in code
            assert "model =" in code
    
    def test_stairs_keywords(self):
        """Test generation for stairs-related keywords"""
        for keyword in ['stairs', 'staircase', 'steps']:
            code = generate_smart_fallback_badcad_code(f"create {keyword}")
            assert "from badcad import *" in code
            assert "step" in code.lower()
            assert "move" in code
            assert "model =" in code
    
    def test_cross_keywords(self):
        """Test generation for cross-related keywords"""
        for keyword in ['cross', 'plus sign', '+']:
            code = generate_smart_fallback_badcad_code(f"make a {keyword}")
            assert "from badcad import *" in code
            assert "horizontal" in code or "vertical" in code
            assert "model =" in code
    
    def test_default_fallback(self):
        """Test default fallback for unrecognized prompts"""
        code = generate_smart_fallback_badcad_code("create something random")
        assert "from badcad import *" in code
        assert "box" in code or "square" in code
        assert "model =" in code
    
    def test_case_insensitive_matching(self):
        """Test that keyword matching is case insensitive"""
        code_lower = generate_smart_fallback_badcad_code("create a sphere")
        code_upper = generate_smart_fallback_badcad_code("CREATE A SPHERE")
        code_mixed = generate_smart_fallback_badcad_code("Create A SpHeRe")
        
        assert "sphere(" in code_lower
        assert "sphere(" in code_upper
        assert "sphere(" in code_mixed


class TestGenerateHardcodedBadCADCode:
    """Test the generate_hardcoded_badcad_code function"""
    
    def test_hardcoded_code(self):
        """Test generation of hardcoded BadCAD code"""
        code = generate_hardcoded_badcad_code()
        
        assert "from badcad import *" in code
        assert "model =" in code
        assert "square" in code
        assert "extrude" in code
        
        # Verify it's valid Python
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError:
            pytest.fail("Generated code has syntax errors")