import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from vibe_dj.api.dependencies import get_config, get_navidrome_sync_service
from vibe_dj.models import Config
from vibe_dj.services import NavidromeSyncService

router = APIRouter(prefix="/api", tags=["config"])


class ConfigResponse(BaseModel):
    """Current configuration response.

    Returns non-sensitive configuration values.
    Password is never returned, only a boolean indicating if it's set.
    """

    music_library: str
    navidrome_url: Optional[str] = None
    navidrome_username: Optional[str] = None
    has_navidrome_password: bool = False


class ValidatePathRequest(BaseModel):
    """Request to validate a filesystem path."""

    path: str


class ValidatePathResponse(BaseModel):
    """Response for path validation."""

    valid: bool
    exists: bool
    is_directory: bool
    message: str


class TestNavidromeRequest(BaseModel):
    """Request to test Navidrome connection."""

    url: str
    username: str
    password: str


class TestNavidromeResponse(BaseModel):
    """Response for Navidrome connection test."""

    success: bool
    message: str


@router.get("/config", response_model=ConfigResponse)
def get_current_config(
    config: Config = Depends(get_config),
) -> ConfigResponse:
    """Get current application configuration.

    Returns non-sensitive configuration values. Password is never returned.

    :param config: Application configuration
    :return: Current configuration values
    """
    return ConfigResponse(
        music_library=config.music_library,
        navidrome_url=config.navidrome_url,
        navidrome_username=config.navidrome_username,
        has_navidrome_password=bool(config.navidrome_password),
    )


@router.post("/config/validate-path", response_model=ValidatePathResponse)
def validate_path(request: ValidatePathRequest) -> ValidatePathResponse:
    """Validate a filesystem path for use as music library.

    Checks if the path exists and is a directory.

    :param request: Path validation request
    :return: Validation result
    """
    path = request.path.strip()

    if not path:
        return ValidatePathResponse(
            valid=False,
            exists=False,
            is_directory=False,
            message="Path cannot be empty",
        )

    exists = os.path.exists(path)
    is_directory = os.path.isdir(path) if exists else False

    if not exists:
        return ValidatePathResponse(
            valid=False,
            exists=False,
            is_directory=False,
            message=f"Path does not exist: {path}",
        )

    if not is_directory:
        return ValidatePathResponse(
            valid=False,
            exists=True,
            is_directory=False,
            message=f"Path is not a directory: {path}",
        )

    return ValidatePathResponse(
        valid=True,
        exists=True,
        is_directory=True,
        message="Path is valid",
    )


@router.post("/navidrome/test", response_model=TestNavidromeResponse)
def test_navidrome_connection(
    request: TestNavidromeRequest,
) -> TestNavidromeResponse:
    """Test connection to Navidrome server.

    Attempts to authenticate with the provided credentials.

    :param request: Navidrome connection test request
    :return: Connection test result
    """
    from vibe_dj.services.navidrome_client import NavidromeClient

    try:
        client = NavidromeClient(
            base_url=request.url,
            username=request.username,
            password=request.password,
        )

        # Try to ping the server
        if client.ping():
            return TestNavidromeResponse(
                success=True,
                message="Successfully connected to Navidrome server",
            )
        else:
            return TestNavidromeResponse(
                success=False,
                message="Failed to connect to Navidrome server",
            )

    except Exception as e:
        logger.error(f"Navidrome connection test failed: {e}")
        return TestNavidromeResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
        )
