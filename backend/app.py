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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description="Generate 3D CAD models from text descriptions using AI and BadCAD",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
            "storage": "available",
        },
    }


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
            "admin": "/api/admin/collected-emails",
        },
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
        logger.error(f"❌ BadCAD Executor service failed: {e}")

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

        cleanup_count = model_storage.cleanup_old_models()
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
        access_log=True,
    )
