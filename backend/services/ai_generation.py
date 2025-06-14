"""
AI Generation service for creating BadCAD code using Gemini AI
"""
from typing import Optional, Dict, List, Any
import logging

from core.config import settings, GEMINI_AVAILABLE, gemini_client
from core.exceptions import AIGenerationError, ConfigurationError
from utils.code_extraction import extract_badcad_code, validate_badcad_code, clean_code
from utils.stl_fallback import generate_smart_fallback_badcad_code, generate_hardcoded_badcad_code

logger = logging.getLogger(__name__)


class AICodeGenerator:
    """Service for generating BadCAD code using AI models"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the AI code generator.
        
        Args:
            model_name: Name of the AI model to use (defaults to settings)
        """
        self.model_name = model_name or settings.gemini_model
        self.client = gemini_client
        self.available = GEMINI_AVAILABLE
        
    def generate_badcad_code(self, prompt: str, validate: bool = True) -> str:
        """
        Generate BadCAD code from a natural language prompt.
        
        Args:
            prompt: Natural language description of the 3D model
            validate: Whether to validate the generated code
            
        Returns:
            Generated BadCAD code
            
        Raises:
            AIGenerationError: If generation fails
        """
        if not prompt or not prompt.strip():
            raise AIGenerationError("Prompt cannot be empty", prompt=prompt)
        
        logger.info(f"Generating BadCAD code for prompt: '{prompt[:100]}...'")
        
        try:
            if not self.available:
                logger.warning("Gemini not available, using fallback")
                return self._generate_fallback_code(prompt)
            
            # Generate code using AI
            code = self._generate_with_gemini(prompt)
            
            # Clean and validate the code
            code = clean_code(code)
            
            if validate:
                is_valid, error_msg = validate_badcad_code(code)
                if not is_valid:
                    logger.warning(f"Generated code validation failed: {error_msg}")
                    logger.info("Falling back to smart fallback generation")
                    return self._generate_fallback_code(prompt)
            
            logger.info(f"Successfully generated BadCAD code ({len(code)} chars)")
            return code
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI generation failed: {error_msg}")
            
            # Check for specific error types and provide helpful fallback
            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                logger.info("Quota exhausted - using fallback generation")
                return self._generate_fallback_code(prompt)
            elif "PERMISSION_DENIED" in error_msg:
                logger.error("Permission denied - check API key")
                return self._generate_fallback_code(prompt)
            else:
                logger.error(f"General AI error: {error_msg}")
                return self._generate_fallback_code(prompt)
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """Generate code using Gemini AI"""
        if not self.client:
            raise ConfigurationError("Gemini client not initialized", missing_config="GEMINI_API_KEY")
        
        # Build the full prompt with system instructions and examples
        full_prompt = self._build_full_prompt(prompt)
        
        try:
            logger.debug(f"Sending request to Gemini model: {self.model_name}")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            response_text = response.text if response.text else ""
            logger.debug(f"Gemini response: {response_text[:200]}...")
            
            if not response_text:
                raise AIGenerationError("Empty response from Gemini API")
            
            # Extract code from response
            badcad_code = extract_badcad_code(response_text)
            
            if not badcad_code:
                raise AIGenerationError("No valid code found in AI response", original_error=response_text[:500])
            
            return badcad_code
            
        except Exception as e:
            raise AIGenerationError(f"Gemini API call failed: {str(e)}", prompt=prompt, original_error=str(e))
    
    def _generate_fallback_code(self, prompt: str) -> str:
        """Generate fallback code when AI is unavailable"""
        logger.info("Using smart fallback code generation")
        return generate_smart_fallback_badcad_code(prompt)
    
    def _build_full_prompt(self, user_prompt: str) -> str:
        """Build the complete prompt with system instructions and examples"""
        system_prompt = self._get_system_prompt()
        examples = self._get_few_shot_examples()
        
        # Build the message with few-shot examples
        user_message = "Here are some examples of BadCAD code generation:\\n\\n"
        
        for example in examples:
            user_message += f"Prompt: {example['prompt']}\\nBadCAD Code:\\n```python\\n{example['code']}\\n```\\n\\n"
        
        user_message += f"Now generate BadCAD code for this prompt: {user_prompt}\\n\\nBadCAD Code:"
        
        # Combine system prompt and user message
        return f"{system_prompt}\\n\\n{user_message}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for BadCAD code generation"""
        return """You are an expert at generating BadCAD code for 3D CAD modeling. BadCAD is a Python library for creating 3D models using constructive solid geometry.

CORE BadCAD API:

2D Shapes (return Shape objects):
- square(x, y, center=False) - rectangle
- circle(r=None, d=None, fn=0) - circle
- polygon(points) - custom polygon

3D Primitives (return Solid objects):
- cube(x, y, z, center=False) - box
- cylinder(h, r=None, d=None, center=False, fn=0) - cylinder
- sphere(r=None, d=None, fn=0) - sphere
- conic(h, r1, r2, center=False, fn=0) - truncated cone (for cones, use r2=0.001 not 0)

Shape Operations:
- .extrude(height, center=False) - 2D to 3D
- .revolve(z=360, fn=0) - revolve around Z axis
- .extrude_to(other_shape, height) - morph between shapes
- .offset(delta, join_type='miter') - inset/outset (join_type: 'miter', 'round', 'square')

Transformations:
- .move(x=0, y=0, z=0) - translate (Solids need z, Shapes need x,y)
- .rotate(x=0, y=0, z=0) - rotate (Solids: x,y,z, Shapes: z only)
- .scale(x=1, y=1, z=1) - scale (Solids: x,y,z, Shapes: x,y)
- .mirror(x=0, y=0, z=0) - mirror (Solids: x,y,z, Shapes: x,y)
- .align() - align using bounding box (xmin/x/xmax, ymin/y/ymax, zmin/z/zmax)

Boolean Operations:
- + (union), - (subtract), & (intersect)

Special Functions:
- threads(d, h, pitch, starts=1) - generate screw threads
- text(string, size=10, font='Helvetica') - text to 2D shape
- hull(*objects) - convex hull of multiple objects

IMPORTANT RULES:
1. Always end with a variable named 'model' that contains the final result
2. Import: from badcad import *
3. Use .move() for positioning (NOT .translate())
4. Shapes are 2D, Solids are 3D - use .extrude() to convert Shape to Solid
5. Use center=True for centering when available
6. Use parametric designs with variables
7. You have full Python access - use math, loops, functions as needed

Generate ONLY the BadCAD code, no explanations."""
    
    def _get_few_shot_examples(self) -> List[Dict[str, str]]:
        """Get few-shot examples for prompt engineering"""
        return [
            {
                "prompt": "Create a cross shape",
                "code": """from badcad import *
# Cross shape
plus = square(30, 10, center=True) + square(10, 30, center=True)
model = plus.extrude(5)"""
            },
            {
                "prompt": "Create a simple cone",
                "code": """from badcad import *
# Simple cone using extrude_to (more reliable than conic with r2=0)
base_radius = 10
height = 15

base = circle(r=base_radius)
tip = circle(r=0.001)  # Very small circle for tip
model = base.extrude_to(tip, height)"""
            },
            {
                "prompt": "Create a simple staircase with 3 steps",
                "code": """from badcad import *
# Simple staircase with 3 steps
step_width = 30
step_depth = 20
step_height = 8

# Create steps at different positions
step1 = cube(step_width, step_depth, step_height, center=True)
step2 = cube(step_width, step_depth, step_height, center=True).move(0, step_depth, step_height)
step3 = cube(step_width, step_depth, step_height, center=True).move(0, step_depth*2, step_height*2)

# Combine all steps
model = step1 + step2 + step3"""
            },
            {
                "prompt": "Create a washer or ring",
                "code": """from badcad import *
# Washer/ring
outer_radius = 15
inner_radius = 5
thickness = 3

outer = circle(r=outer_radius)
inner = circle(r=inner_radius)
ring = outer - inner
model = ring.extrude(thickness)"""
            },
            {
                "prompt": "Make a hexagonal nut",
                "code": """from badcad import *
import math
# Hexagonal nut
hex_width = 20
thickness = 10
hole_diameter = 12

# Create hexagon
hex_points = []
for i in range(6):
    angle = i * math.pi / 3
    x = (hex_width / 2) * math.cos(angle)
    y = (hex_width / 2) * math.sin(angle)
    hex_points.append((x, y))

hex_shape = polygon(hex_points)
nut = hex_shape.extrude(thickness)

# Create hole
hole = circle(d=hole_diameter).extrude(thickness)

model = nut - hole"""
            },
            {
                "prompt": "Create a bolt with threads",
                "code": """from badcad import *
# Bolt with threads and hex head
thread_diameter = 8
thread_length = 16
pitch = 1.25
head_size = 12
head_height = 5

# Create threaded shaft
shaft = threads(d=thread_diameter, h=thread_length, pitch=pitch)

# Create hex head
hex_head = circle(r=head_size, fn=6).extrude(head_height).move(z=thread_length)

model = shaft + hex_head"""
            }
        ]


# Global instance
ai_generator = AICodeGenerator()