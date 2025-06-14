"""
Text-to-CAD API - Modular FastAPI Application

A FastAPI application that generates 3D CAD models from text descriptions
using AI and BadCAD. This version uses a modular architecture with separate
services for AI generation, BadCAD execution, user management, and storage.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import modular components
from core.config import settings
from api.routes import generation, download, user, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description="Generate 3D CAD models from text descriptions using AI and BadCAD",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route modules
app.include_router(generation.router)
app.include_router(download.router)
app.include_router(user.router)
app.include_router(admin.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns basic system status and configuration info.
    """
    return {
        "status": "healthy",
        "api_title": settings.api_title,
        "version": "2.0.0",
        "architecture": "modular",
        "services": {
            "ai_generation": "available",
            "badcad_executor": "available", 
            "user_management": "available",
            "storage": "available"
        }
    }

<<<<<<< Updated upstream
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
=======
# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Text-to-CAD API v2.0 - Modular Architecture",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "generation": "/api/generate",
            "execution": "/api/execute",
            "download": "/api/download/{model_id}",
            "user_info": "/api/user/info",
            "admin": "/api/admin/collected-emails"
>>>>>>> Stashed changes
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    
    Logs startup information and verifies all services are available.
    """
    logger.info("🚀 Starting Text-to-CAD API v2.0 (Modular Architecture)")
    logger.info(f"📋 Configuration: {settings.api_title}")
    logger.info(f"🔧 Max models per user: {settings.max_models_per_user}")
    
    # Log service availability
    try:
        from services.ai_generation import ai_generator
        logger.info("✅ AI Generation service loaded")
    except Exception as e:
        logger.error(f"❌ AI Generation service failed: {e}")
    
    try:
        from services.badcad_executor import badcad_executor
        logger.info("✅ BadCAD Executor service loaded")
    except Exception as e:
<<<<<<< Updated upstream
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
=======
        logger.error(f"❌ BadCAD Executor service failed: {e}")
>>>>>>> Stashed changes
    
    try:
        from services.user_management import user_manager
        logger.info("✅ User Management service loaded")
    except Exception as e:
        logger.error(f"❌ User Management service failed: {e}")
    
    try:
        from services.storage import model_storage
        logger.info("✅ Storage service loaded")
    except Exception as e:
        logger.error(f"❌ Storage service failed: {e}")
    
    logger.info("🌟 All services initialized - API ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.
    
    Performs cleanup and logs shutdown information.
    """
    logger.info("🛑 Shutting down Text-to-CAD API v2.0")
    
    # Clean up any temporary files
    try:
        from services.storage import model_storage
        cleanup_count = model_storage.cleanup_old_models(max_age_hours=24)
        logger.info(f"🧹 Cleaned up {cleanup_count} temporary model files")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup warning: {e}")
    
    logger.info("✅ Shutdown complete")

# Application entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Text-to-CAD API server...")
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
