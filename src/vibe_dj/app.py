import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .api.routes import index_router, playlist_router, songs_router
from .core import MusicDatabase
from .models import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Handles startup and shutdown tasks including database initialization.
    
    :param app: FastAPI application instance
    """
    logger.info("Starting Vibe-DJ API server")
    
    try:
        config = Config()
        if os.path.exists("config.json"):
            config = Config.from_file("config.json")
        
        with MusicDatabase(config) as db:
            db.init_db()
            logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    logger.info("Shutting down Vibe-DJ API server")


app = FastAPI(
    title="Vibe-DJ API",
    description="Music library indexer and intelligent playlist generator using audio feature analysis",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent JSON responses.
    
    :param request: Request object
    :param exc: HTTPException instance
    :return: JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions.
    
    :param request: Request object
    :param exc: Exception instance
    :return: JSON response with error details
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
        },
    )


@app.get("/")
def root():
    """Root endpoint with API information.
    
    :return: API information and available endpoints
    """
    return {
        "name": "Vibe-DJ API",
        "version": "0.1.0",
        "description": "Music library indexer and intelligent playlist generator",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "index": "/api/index",
            "status": "/api/status/{job_id}",
            "playlist": "/api/playlist",
            "songs": "/api/songs",
        },
    }


@app.get("/health")
def health_check():
    """Health check endpoint.
    
    Verifies database connectivity and FAISS index availability.
    
    :return: Health status information
    """
    try:
        config = Config()
        if os.path.exists("config.json"):
            config = Config.from_file("config.json")
        
        db_status = "disconnected"
        try:
            with MusicDatabase(config) as db:
                db.connection.cursor().execute("SELECT 1")
                db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"error: {str(e)}"
        
        faiss_status = "not_loaded"
        if os.path.exists(config.faiss_index_path):
            faiss_status = "available"
        else:
            faiss_status = "not_found"
        
        overall_status = "ok" if db_status == "connected" else "degraded"
        
        return {
            "status": overall_status,
            "database": db_status,
            "faiss_index": faiss_status,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "database": "error",
            "faiss_index": "error",
            "message": str(e),
        }


app.include_router(index_router)
app.include_router(playlist_router)
app.include_router(songs_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "vibe_dj.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
