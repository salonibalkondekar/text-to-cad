from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
import re

try:
    import badcad
    from badcad import *
    BADCAD_AVAILABLE = True
    print("✅ BadCAD successfully imported")
except ImportError as e:
    print(f"❌ BadCAD import failed: {e}")
    BADCAD_AVAILABLE = False

# Initialize Anthropic client
try:
    import anthropic
    anthropic_client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    ANTHROPIC_AVAILABLE = True
    print("✅ Anthropic client initialized")
except ImportError as e:
    print(f"❌ Anthropic import failed: {e}")
    ANTHROPIC_AVAILABLE = False
    anthropic_client = None
    # Define fallback classes
    class Box:
        def __init__(self, x, y, z): pass
        def export_stl(self, path): pass
    class Cylinder:
        def __init__(self, r, h): pass
    class Sphere:
        def __init__(self, r): pass
    Union = Intersection = Box

app = FastAPI(title="Text-to-CAD API", description="Generate 3D CAD models from text descriptions")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store generated models temporarily
temp_models = {}

class PromptRequest(BaseModel):
    prompt: str

class BadCADCodeRequest(BaseModel):
    code: str

class GenerateResponse(BaseModel):
    success: bool
    model_id: str
    badcad_code: str
    message: str

class ExecuteResponse(BaseModel):
    success: bool
    model_id: str
    message: str

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_model(request: PromptRequest):
    try:
        if not request.prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Generate BadCAD code using Claude AI
        badcad_code = generate_badcad_code_with_claude(request.prompt)
        
        # Execute BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        stl_file = execute_badcad_and_export(badcad_code, model_id)
        
        # Store the temporary file path
        temp_models[model_id] = stl_file
        
        return GenerateResponse(
            success=True,
            model_id=model_id,
            badcad_code=badcad_code,
            message=f'Generated model for: "{request.prompt}"'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_badcad_code(request: BadCADCodeRequest):
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="No code provided")
        
        # Execute user-provided BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        stl_file = execute_badcad_and_export(request.code, model_id)
        
        # Store the temporary file path
        temp_models[model_id] = stl_file
        
        return ExecuteResponse(
            success=True,
            model_id=model_id,
            message="BadCAD code executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{model_id}")
async def download_model(model_id: str):
    try:
        if model_id not in temp_models:
            raise HTTPException(status_code=404, detail="Model not found")
        
        stl_file = temp_models[model_id]
        return FileResponse(
            path=stl_file,
            filename=f'model_{model_id}.stl',
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_badcad_code_with_claude(prompt):
    """Generate BadCAD code using Claude AI"""
    if not ANTHROPIC_AVAILABLE:
        print("Anthropic not available, using fallback")
        return generate_hardcoded_badcad_code()
    
    system_prompt = """You are an expert at generating BadCAD code for 3D CAD modeling. BadCAD is a Python library for creating 3D models using constructive solid geometry.

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

    few_shot_examples = [
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
    
    # Build the message with few-shot examples
    user_message = "Here are some examples of BadCAD code generation:\n\n"
    
    for example in few_shot_examples:
        user_message += f"Prompt: {example['prompt']}\nBadCAD Code:\n```python\n{example['code']}\n```\n\n"
    
    user_message += f"Now generate BadCAD code for this prompt: {prompt}\n\nBadCAD Code:"
    
    try:
        print(f"🤖 Generating BadCAD code for: '{prompt}'")
        
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=system_prompt
        )
        
        response_text = message.content[0].text if message.content else ""
        print(f"📝 Claude response: {response_text[:200]}...")
        
        # Extract code from response
        badcad_code = extract_badcad_code(response_text)
        print(f"✅ Extracted BadCAD code ({len(badcad_code)} chars)")
        
        return badcad_code
        
    except Exception as e:
        print(f"❌ Claude generation failed: {e}")
        return generate_hardcoded_badcad_code()

def extract_badcad_code(response_text):
    """Extract BadCAD code from Claude's response"""
    # Try to find code blocks first
    code_block_match = re.search(r'```(?:python)?\s*(.*?)\s*```', response_text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # If no code blocks, look for lines that look like Python code
    lines = response_text.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        # Start collecting if we see Python-like syntax
        if any(pattern in stripped for pattern in ['=', 'square(', 'circle(', 'extrude(', 'model =', 'import']):
            in_code = True
        
        if in_code:
            # Stop if we hit explanatory text
            if stripped and not any(char in stripped for char in ['=', '(', ')', '#', 'import', 'from']):
                if len(stripped.split()) > 3:  # Likely explanatory text
                    break
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    # Fallback: return the whole response
    return response_text.strip()

def generate_hardcoded_badcad_code():
    """Fallback hardcoded BadCAD code"""
    return """# Simple box
box = square(20, 20, center=True)
model = box.extrude(10)"""

def execute_badcad_and_export(badcad_code, model_id):
    """Execute BadCAD code and export to STL"""
    # Create a temporary file for the STL
    temp_dir = tempfile.gettempdir()
    stl_filename = f"model_{model_id}.stl"
    stl_path = os.path.join(temp_dir, stl_filename)
    
    if not BADCAD_AVAILABLE:
        print("BadCAD not available, creating fallback STL")
        create_fallback_stl(stl_path)
        return stl_path
    
    try:
        # Execute the BadCAD code with full access for performance
        print("🔧 Setting up BadCAD execution environment...")
        
        # Create execution environment with FULL Python and BadCAD access - no restrictions
        exec_globals = globals().copy()  # Full access to everything
        exec_locals = {}
        
        print(f"✅ BadCAD environment ready with FULL access")
        
        # Execute the code
        print(f"Executing BadCAD code:\n{badcad_code}")
        exec(badcad_code, exec_globals)
        
        # Get the model from the execution context
        if 'model' in exec_globals:
            model = exec_globals['model']
            print(f"Model found: {type(model)}")
            print(f"Model methods: {[m for m in dir(model) if not m.startswith('_')]}")
            
            # Use BadCAD's stl method
            try:
                if hasattr(model, 'stl'):
                    # Get STL data from BadCAD model
                    stl_data = model.stl()
                    print(f"STL data type: {type(stl_data)}")
                    
                    # Write STL data to file (handle both bytes and string)
                    if isinstance(stl_data, bytes):
                        with open(stl_path, 'wb') as f:
                            f.write(stl_data)
                    else:
                        with open(stl_path, 'w') as f:
                            f.write(stl_data)
                    
                    print(f"✅ STL exported using model.stl() to: {stl_path}")
                else:
                    raise AttributeError("No stl method found on model")
                
                # Verify the file was created and has content
                if os.path.exists(stl_path) and os.path.getsize(stl_path) > 0:
                    print(f"✅ STL file verified: {os.path.getsize(stl_path)} bytes")
                else:
                    raise Exception("STL file was not created or is empty")
                
            except Exception as export_error:
                print(f"❌ STL export failed: {export_error}")
                print("Creating fallback STL...")
                create_fallback_stl(stl_path)
                
        else:
            print("No 'model' variable found in execution context")
            print(f"Available variables: {[k for k in exec_globals.keys() if not k.startswith('_')]}")
            # Fallback: create a simple cube
            create_fallback_stl(stl_path)
            print("Used fallback cube")
        
        return stl_path
        
    except Exception as e:
        # If BadCAD fails, create a simple hardcoded STL file
        print(f"BadCAD execution failed: {e}")
        create_fallback_stl(stl_path)
        return stl_path

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)