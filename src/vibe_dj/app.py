import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy import select

from .api.routes import (
    config_router,
    index_router,
    library_router,
    playlist_router,
    profiles_router,
    songs_router,
)
from .core import MusicDatabase
from .core.profile_database import ProfileDatabase
from .models import Config


def _initialize_profiles(config: Config) -> None:
    """Initialize the profile database and migrate existing Navidrome credentials.

    Creates the profiles database, ensures the 'Shared' profile exists, and
    migrates any existing Navidrome credentials from config.json into the
    'Shared' profile if they have not already been migrated.

    :param config: Application configuration with optional Navidrome credentials
    """
    db_path = os.environ.get("VIBE_DJ_PROFILES_DB", "profiles.db")
    encryption_key = os.environ.get("VIBE_DJ_ENCRYPTION_KEY")

    with ProfileDatabase(db_path=db_path, encryption_key=encryption_key) as profile_db:
        profile_db.init_db()
        logger.info("Profile database initialized")

        shared = profile_db.get_profile_by_name(ProfileDatabase.SHARED_PROFILE_NAME)
        if shared is None:
            logger.warning("Shared profile not found after init_db — skipping migration")
            return

        has_credentials = config.navidrome_url or config.navidrome_username or config.navidrome_password
        already_migrated = shared.subsonic_url or shared.subsonic_username or shared.subsonic_password_encrypted

        if has_credentials and not already_migrated:
            logger.info("Migrating existing Navidrome credentials to 'Shared' profile")
            profile_db.update_profile(
                shared.id,
                subsonic_url=config.navidrome_url,
                subsonic_username=config.navidrome_username,
                subsonic_password=config.navidrome_password,
            )
            logger.info("Navidrome credentials migrated to 'Shared' profile")
        else:
            logger.info("Profile migration skipped (no credentials or already migrated)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown tasks including database initialization.

    :param app: FastAPI application instance
    """
    logger.info("Starting Vibe-DJ server")

    try:
        config = Config()
        if os.path.exists("config.json"):
            config = Config.from_file("config.json")

        with MusicDatabase(config) as db:
            db.init_db()
            logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    try:
        config = Config()
        if os.path.exists("config.json"):
            config = Config.from_file("config.json")

        _initialize_profiles(config)
    except Exception as e:
        logger.error(f"Failed to initialize profile database: {e}")

    yield

    logger.info("Shutting down Vibe-DJ server")


app = FastAPI(
    title="Vibe-DJ",
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


# Root endpoint is only registered if the UI is not available
# When UI is available, the static file mount will serve index.html at "/"
# Check env var first (Docker non-editable install), then fall back to __file__-relative (local dev)
_ui_env = os.environ.get("VIBE_DJ_UI_PATH")
ui_dist_path = (
    Path(_ui_env) if _ui_env else Path(__file__).parent.parent.parent / "ui" / "dist"
)
if not ui_dist_path.exists():

    @app.get("/")
    def root():
        """Root endpoint with API information.

        :return: API information and available endpoints
        """
        return {
            "name": "Vibe-DJ",
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
                db.session.execute(select(1))
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


app.include_router(config_router)
app.include_router(index_router)
app.include_router(library_router)
app.include_router(playlist_router)
app.include_router(profiles_router)
app.include_router(songs_router)

# Serve the React UI static files if they exist
# The UI is built and placed in ui/dist during the Docker build
# Note: ui_dist_path is defined earlier in the file
if ui_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(ui_dist_path), html=True), name="ui")
    logger.info(f"Serving UI from {ui_dist_path}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "vibe_dj.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
