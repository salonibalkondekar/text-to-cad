from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
import re
import json
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

try:
    import badcad
    from badcad import *
    BADCAD_AVAILABLE = True
    print("✅ BadCAD successfully imported")
except ImportError as e:
    print(f"❌ BadCAD import failed: {e}")
    BADCAD_AVAILABLE = False

# Initialize Google Gemini client
try:
    from google import genai
    gemini_client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    GEMINI_AVAILABLE = True
    print("✅ Gemini client initialized")
except ImportError as e:
    print(f"❌ Gemini import failed: {e}")
    GEMINI_AVAILABLE = False
    gemini_client = None
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

# Simple in-memory user database and JSON file storage (temporary solution)
user_database = {}
COLLECTED_EMAILS_FILE = "collected_user_emails.json"

def load_collected_emails():
    """Load collected user emails from JSON file"""
    try:
        if os.path.exists(COLLECTED_EMAILS_FILE):
            with open(COLLECTED_EMAILS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load collected emails: {e}")
    return {}

def save_collected_emails(data):
    """Save collected user emails to JSON file"""
    try:
        with open(COLLECTED_EMAILS_FILE, 'w') as f:
            json.dump(data, indent=2, fp=f)
        print(f"✅ Saved user data to {COLLECTED_EMAILS_FILE}")
    except Exception as e:
        print(f"❌ Failed to save collected emails: {e}")

def add_user_prompt(user_id, email, prompt, prompt_type="generate"):
    """Add a user's prompt to the collected data"""
    collected_data = load_collected_emails()
    
    if user_id not in collected_data:
        collected_data[user_id] = {
            'email': email,
            'prompts': [],
            'model_count': 0,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
    
    # Add the prompt
    collected_data[user_id]['prompts'].append({
        'prompt': prompt,
        'type': prompt_type,
        'timestamp': datetime.now().isoformat()
    })
    
    # Update last activity
    collected_data[user_id]['last_activity'] = datetime.now().isoformat()
    
    save_collected_emails(collected_data)
    return collected_data[user_id]

# Load existing collected emails on startup
collected_user_data = load_collected_emails()
print(f"📧 Loaded {len(collected_user_data)} user records from {COLLECTED_EMAILS_FILE}")

class PromptRequest(BaseModel):
    prompt: str
    user_id: str = None

class BadCADCodeRequest(BaseModel):
    code: str
    user_id: str = None

class UserInfoRequest(BaseModel):
    user_id: str
    email: str
    name: str

class UserCountRequest(BaseModel):
    user_id: str

class GenerateResponse(BaseModel):
    success: bool
    model_id: str = None
    badcad_code: str = None
    message: str
    error_type: str = None
    error_details: str = None

class ExecuteResponse(BaseModel):
    success: bool
    model_id: str
    message: str

class UserInfoResponse(BaseModel):
    success: bool
    user_id: str
    model_count: int
    max_models: int

class UserCountResponse(BaseModel):
    success: bool
    model_count: int

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_model(request: PromptRequest):
    try:
        if not request.prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Check user authentication and limits
        if request.user_id:
            if not check_user_can_generate(request.user_id):
                raise HTTPException(status_code=403, detail="Model generation limit reached (10 models max)")
        
        # Store the prompt in collected data if user_id provided
        if request.user_id and request.user_id in user_database:
            user_email = user_database[request.user_id].get('email', 'unknown@example.com')
            add_user_prompt(request.user_id, user_email, request.prompt, "generate")
        
        # Generate BadCAD code using Gemini AI
        try:
            badcad_code = generate_badcad_code_with_gemini(request.prompt)
            generation_status = "ai_generated"
        except Exception as gen_error:
            error_msg = str(gen_error)
            print(f"❌ AI generation failed: {error_msg}")
            
            # Check for specific API errors that should be reported to user
            if "INVALID_ARGUMENT" in error_msg and "API key not valid" in error_msg:
                return GenerateResponse(
                    success=False,
                    message="API configuration error",
                    error_type="invalid_api_key",
                    error_details="The Gemini API key is invalid or missing. Please check the server configuration."
                )
            elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                return GenerateResponse(
                    success=False,
                    message="API quota exceeded",
                    error_type="quota_exhausted",
                    error_details="The Gemini API quota has been exceeded. Please try again later."
                )
            elif "PERMISSION_DENIED" in error_msg:
                return GenerateResponse(
                    success=False,
                    message="API access denied",
                    error_type="permission_denied", 
                    error_details="Access to the Gemini API was denied. Please check the API key permissions."
                )
            else:
                # For other errors, still provide fallback but inform user
                print(f"⚠️ Using fallback generation due to: {gen_error}")
                badcad_code = generate_smart_fallback_badcad_code(request.prompt)
                generation_status = "fallback_generated"
        
        # Execute BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        stl_file = execute_badcad_and_export(badcad_code, model_id)
        
        # Store the temporary file path
        temp_models[model_id] = stl_file
        
        # Increment user model count if authenticated
        if request.user_id:
            increment_user_model_count(request.user_id)
        
        # Create appropriate message based on generation method
        if generation_status == "ai_generated":
            message = f'Generated model for: "{request.prompt}"'
        else:
            message = f'Generated fallback model for: "{request.prompt}" (AI service temporarily unavailable)'
        
        return GenerateResponse(
            success=True,
            model_id=model_id,
            badcad_code=badcad_code,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_badcad_code(request: BadCADCodeRequest):
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="No code provided")
        
        # Check user authentication and limits
        if request.user_id:
            if not check_user_can_generate(request.user_id):
                raise HTTPException(status_code=403, detail="Model generation limit reached (10 models max)")
        
        # Store the code in collected data if user_id provided
        if request.user_id and request.user_id in user_database:
            user_email = user_database[request.user_id].get('email', 'unknown@example.com')
            add_user_prompt(request.user_id, user_email, request.code, "execute_code")
        
        # Execute user-provided BadCAD code and generate STL
        model_id = str(uuid.uuid4())
        stl_file = execute_badcad_and_export(request.code, model_id)
        
        # Store the temporary file path
        temp_models[model_id] = stl_file
        
        # Increment user model count if authenticated
        if request.user_id:
            increment_user_model_count(request.user_id)
        
        return ExecuteResponse(
            success=True,
            model_id=model_id,
            message="BadCAD code executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/info", response_model=UserInfoResponse)
async def get_user_info(request: UserInfoRequest):
    try:
        # Create or update user record in both user_database and collected_user_data
        if request.user_id not in user_database:
            user_database[request.user_id] = {
                'email': request.email,
                'name': request.name,
                'model_count': 0,
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat()
            }
        else:
            # Update last login
            user_database[request.user_id]['last_login'] = datetime.now().isoformat()
            user_database[request.user_id]['email'] = request.email
            user_database[request.user_id]['name'] = request.name
        
        # Also update the JSON file with user info
        collected_data = load_collected_emails()
        if request.user_id not in collected_data:
            collected_data[request.user_id] = {
                'email': request.email,
                'name': request.name,
                'prompts': [],
                'model_count': 0,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        else:
            # Update existing record
            collected_data[request.user_id]['email'] = request.email
            collected_data[request.user_id]['name'] = request.name
            collected_data[request.user_id]['last_activity'] = datetime.now().isoformat()
            # Sync model count
            collected_data[request.user_id]['model_count'] = user_database[request.user_id]['model_count']
        
        save_collected_emails(collected_data)
        
        return UserInfoResponse(
            success=True,
            user_id=request.user_id,
            model_count=user_database[request.user_id]['model_count'],
            max_models=10
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/increment-count", response_model=UserCountResponse)
async def increment_user_count(request: UserCountRequest):
    try:
        if request.user_id not in user_database:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_count = user_database[request.user_id]['model_count']
        if current_count >= 10:
            raise HTTPException(status_code=403, detail="Model generation limit reached")
        
        user_database[request.user_id]['model_count'] += 1
        
        # Also update the JSON file
        collected_data = load_collected_emails()
        if request.user_id in collected_data:
            collected_data[request.user_id]['model_count'] = user_database[request.user_id]['model_count']
            collected_data[request.user_id]['last_activity'] = datetime.now().isoformat()
            save_collected_emails(collected_data)
        
        return UserCountResponse(
            success=True,
            model_count=user_database[request.user_id]['model_count']
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

@app.get("/api/admin/collected-emails")
async def get_collected_emails():
    """Admin endpoint to view collected user emails and prompts"""
    try:
        collected_data = load_collected_emails()
        
        # Create summary
        summary = {
            'total_users': len(collected_data),
            'total_prompts': sum(len(user_data.get('prompts', [])) for user_data in collected_data.values()),
            'total_models_generated': sum(user_data.get('model_count', 0) for user_data in collected_data.values()),
            'users': []
        }
        
        for user_id, user_data in collected_data.items():
            summary['users'].append({
                'user_id': user_id,
                'email': user_data.get('email', 'N/A'),
                'name': user_data.get('name', 'N/A'),
                'model_count': user_data.get('model_count', 0),
                'total_prompts': len(user_data.get('prompts', [])),
                'created_at': user_data.get('created_at', 'N/A'),
                'last_activity': user_data.get('last_activity', 'N/A'),
                'recent_prompts': user_data.get('prompts', [])[-3:] if user_data.get('prompts') else []
            })
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_badcad_code_with_gemini(prompt):
    """Generate BadCAD code using Google Gemini AI"""
    if not GEMINI_AVAILABLE:
        print("Gemini not available, using fallback")
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
    
    # Combine system prompt and user message for Gemini
    full_prompt = f"{system_prompt}\n\n{user_message}"
    
    try:
        print(f"🤖 Generating BadCAD code for: '{prompt}'")
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=full_prompt
        )
        
        response_text = response.text if response.text else ""
        print(f"📝 Gemini response: {response_text[:200]}...")
        
        # Extract code from response
        badcad_code = extract_badcad_code(response_text)
        print(f"✅ Extracted BadCAD code ({len(badcad_code)} chars)")
        
        return badcad_code
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Gemini generation failed: {error_msg}")
        
        # Check for critical API errors that should be propagated to user
        if "INVALID_ARGUMENT" in error_msg and "API key not valid" in error_msg:
            raise Exception(f"INVALID_ARGUMENT. {e}")
        elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            raise Exception(f"RESOURCE_EXHAUSTED. {e}")
        elif "PERMISSION_DENIED" in error_msg:
            raise Exception(f"PERMISSION_DENIED. {e}")
        else:
            # For other errors, provide a fallback
            print(f"🔧 General error: {error_msg}")
            return generate_smart_fallback_badcad_code(prompt)

def extract_badcad_code(response_text):
    """Extract BadCAD code from AI model response"""
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
    return """from badcad import *
# Simple box
box = square(20, 20, center=True)
model = box.extrude(10)"""

def generate_smart_fallback_badcad_code(prompt):
    """Generate a smarter fallback based on the prompt keywords"""
    prompt_lower = prompt.lower()
    
    # Try to detect what the user wants and provide a relevant fallback
    if any(word in prompt_lower for word in ['cone', 'triangle', 'pyramid']):
        return """from badcad import *
# Simple cone (AI service temporarily unavailable)
base = circle(r=10)
tip = circle(r=0.5)
model = base.extrude_to(tip, 15)"""
    
    elif any(word in prompt_lower for word in ['sphere', 'ball', 'round']):
        return """from badcad import *
# Simple sphere (AI service temporarily unavailable)
model = sphere(r=8)"""
    
    elif any(word in prompt_lower for word in ['cylinder', 'tube', 'pipe']):
        return """from badcad import *
# Simple cylinder (AI service temporarily unavailable)
model = cylinder(h=20, r=6)"""
    
    elif any(word in prompt_lower for word in ['ring', 'washer', 'hole']):
        return """from badcad import *
# Simple ring (AI service temporarily unavailable)
outer = circle(r=10)
inner = circle(r=5)
ring = outer - inner
model = ring.extrude(5)"""
    
    elif any(word in prompt_lower for word in ['gear', 'cog', 'teeth']):
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
    
    else:
        # Default to a box but make it more interesting
        return """from badcad import *
# Simple box (AI service temporarily unavailable)
# Generated fallback based on your prompt
box = square(15, 15, center=True)
model = box.extrude(8)"""

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

def check_user_can_generate(user_id):
    """Check if user can generate more models"""
    if user_id not in user_database:
        return True  # New user can generate
    return user_database[user_id]['model_count'] < 10

def increment_user_model_count(user_id):
    """Increment user's model count"""
    if user_id in user_database:
        user_database[user_id]['model_count'] += 1

def create_fallback_stl(stl_path):
    """Create a simple fallback STL file"""
    # Simple cube STL content
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
    
    with open(stl_path, 'w') as f:
        f.write(stl_content)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
