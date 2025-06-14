"""
STL fallback generation utilities
"""
import os
from typing import Dict, Callable


def create_fallback_stl(stl_path: str) -> None:
    """
    Create a simple fallback STL file (cube).
    
    Args:
        stl_path: Path where the STL file should be created
    """
    stl_content = """solid cube
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex -1.0 1.0 1.0
      vertex -1.0 -1.0 1.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex -1.0 -1.0 1.0
      vertex 1.0 -1.0 1.0
    endloop
  endfacet
  facet normal 0.0 0.0 -1.0
    outer loop
      vertex 1.0 -1.0 -1.0
      vertex -1.0 -1.0 -1.0
      vertex -1.0 1.0 -1.0
    endloop
  endfacet
  facet normal 0.0 0.0 -1.0
    outer loop
      vertex 1.0 -1.0 -1.0
      vertex -1.0 1.0 -1.0
      vertex 1.0 1.0 -1.0
    endloop
  endfacet
  facet normal 0.0 1.0 0.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex 1.0 1.0 -1.0
      vertex -1.0 1.0 -1.0
    endloop
  endfacet
  facet normal 0.0 1.0 0.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex -1.0 1.0 -1.0
      vertex -1.0 1.0 1.0
    endloop
  endfacet
  facet normal 0.0 -1.0 0.0
    outer loop
      vertex 1.0 -1.0 1.0
      vertex -1.0 -1.0 1.0
      vertex -1.0 -1.0 -1.0
    endloop
  endfacet
  facet normal 0.0 -1.0 0.0
    outer loop
      vertex 1.0 -1.0 1.0
      vertex -1.0 -1.0 -1.0
      vertex 1.0 -1.0 -1.0
    endloop
  endfacet
  facet normal 1.0 0.0 0.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex 1.0 -1.0 1.0
      vertex 1.0 -1.0 -1.0
    endloop
  endfacet
  facet normal 1.0 0.0 0.0
    outer loop
      vertex 1.0 1.0 1.0
      vertex 1.0 -1.0 -1.0
      vertex 1.0 1.0 -1.0
    endloop
  endfacet
  facet normal -1.0 0.0 0.0
    outer loop
      vertex -1.0 1.0 1.0
      vertex -1.0 1.0 -1.0
      vertex -1.0 -1.0 -1.0
    endloop
  endfacet
  facet normal -1.0 0.0 0.0
    outer loop
      vertex -1.0 1.0 1.0
      vertex -1.0 -1.0 -1.0
      vertex -1.0 -1.0 1.0
    endloop
  endfacet
endsolid cube"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(stl_path), exist_ok=True)
    
    with open(stl_path, 'w') as f:
        f.write(stl_content)


def generate_smart_fallback_badcad_code(prompt: str) -> str:
    """
    Generate a smarter fallback BadCAD code based on prompt keywords.
    
    Args:
        prompt: The user's prompt
        
    Returns:
        BadCAD code that somewhat matches the prompt
    """
    prompt_lower = prompt.lower()
    
    # Define keyword-based generators
    generators: Dict[tuple, Callable[[], str]] = {
        ('cone', 'triangle', 'pyramid'): _generate_cone_code,
        ('sphere', 'ball', 'round', 'orb'): _generate_sphere_code,
        ('cylinder', 'tube', 'pipe', 'rod'): _generate_cylinder_code,
        ('ring', 'washer', 'hole', 'donut', 'torus'): _generate_ring_code,
        ('gear', 'cog', 'teeth', 'sprocket'): _generate_gear_code,
        ('star', 'asterisk'): _generate_star_code,
        ('hexagon', 'hex', 'nut', 'bolt'): _generate_hexagon_code,
        ('stairs', 'staircase', 'steps'): _generate_stairs_code,
        ('cross', 'plus', '+'): _generate_cross_code,
    }
    
    # Check each set of keywords
    for keywords, generator in generators.items():
        if any(word in prompt_lower for word in keywords):
            return generator()
    
    # Default to a simple box
    return _generate_default_box_code()


def _generate_cone_code() -> str:
    """Generate cone BadCAD code"""
    return """from badcad import *
# Simple cone (AI service temporarily unavailable)
base = circle(r=10)
tip = circle(r=0.5)
model = base.extrude_to(tip, 15)"""


def _generate_sphere_code() -> str:
    """Generate sphere BadCAD code"""
    return """from badcad import *
# Simple sphere (AI service temporarily unavailable)
model = sphere(r=8)"""


def _generate_cylinder_code() -> str:
    """Generate cylinder BadCAD code"""
    return """from badcad import *
# Simple cylinder (AI service temporarily unavailable)
model = cylinder(h=20, r=6)"""


def _generate_ring_code() -> str:
    """Generate ring BadCAD code"""
    return """from badcad import *
# Simple ring (AI service temporarily unavailable)
outer = circle(r=10)
inner = circle(r=5)
ring = outer - inner
model = ring.extrude(5)"""


def _generate_gear_code() -> str:
    """Generate gear BadCAD code"""
    return """from badcad import *
# Simple gear (AI service temporarily unavailable)
import math
outer = circle(r=12)
inner = circle(r=8)
gear_base = outer - inner
# Add simple teeth approximation
for i in range(12):
    angle = i * math.pi / 6
    tooth = square(1, 3, center=True)
    tooth = tooth.move(x=10*math.cos(angle), y=10*math.sin(angle))
    gear_base = gear_base + tooth
model = gear_base.extrude(5)"""


def _generate_star_code() -> str:
    """Generate star BadCAD code"""
    return """from badcad import *
# Simple star (AI service temporarily unavailable)
import math
points = []
for i in range(10):
    angle = i * math.pi / 5
    r = 10 if i % 2 == 0 else 5
    points.append((r * math.cos(angle), r * math.sin(angle)))
star = polygon(points)
model = star.extrude(3)"""


def _generate_hexagon_code() -> str:
    """Generate hexagon BadCAD code"""
    return """from badcad import *
# Simple hexagon (AI service temporarily unavailable)
hex_shape = circle(r=10, fn=6)
model = hex_shape.extrude(5)"""


def _generate_stairs_code() -> str:
    """Generate stairs BadCAD code"""
    return """from badcad import *
# Simple staircase (AI service temporarily unavailable)
step_width = 30
step_depth = 20
step_height = 8

# Create 3 steps
step1 = cube(step_width, step_depth, step_height, center=True)
step2 = cube(step_width, step_depth, step_height, center=True).move(0, step_depth, step_height)
step3 = cube(step_width, step_depth, step_height, center=True).move(0, step_depth*2, step_height*2)

model = step1 + step2 + step3"""


def _generate_cross_code() -> str:
    """Generate cross BadCAD code"""
    return """from badcad import *
# Simple cross (AI service temporarily unavailable)
horizontal = square(30, 10, center=True)
vertical = square(10, 30, center=True)
cross = horizontal + vertical
model = cross.extrude(5)"""


def _generate_default_box_code() -> str:
    """Generate default box BadCAD code"""
    return """from badcad import *
# Simple box (AI service temporarily unavailable)
# Generated fallback based on your prompt
box = square(15, 15, center=True)
model = box.extrude(8)"""


def generate_hardcoded_badcad_code() -> str:
    """
    Generate basic hardcoded BadCAD code.
    This is the absolute fallback when nothing else works.
    
    Returns:
        Basic BadCAD code for a simple box
    """
    return """from badcad import *
# Simple box
box = square(20, 20, center=True)
model = box.extrude(10)"""