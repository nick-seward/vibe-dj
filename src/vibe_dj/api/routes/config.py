import json
import os
from typing import Optional

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel

from vibe_dj.api.dependencies import (
    get_config,
    invalidate_config_cache,
)
from vibe_dj.models import Config
from vibe_dj.models.config import ALLOWED_PLAYLIST_SIZES, BPM_JITTER_MAX, BPM_JITTER_MIN
from vibe_dj.services.url_security import UnsafeOutboundURLError, validate_outbound_url

router = APIRouter(prefix="/api", tags=["config"])

CONFIG_FILE_PATH = "config.json"


class ConfigResponse(BaseModel):
    """Current configuration response.

    Returns non-sensitive configuration values.
    Password is never returned, only a boolean indicating if it's set.
    """

    music_library: str
    navidrome_url: Optional[str] = None
    navidrome_username: Optional[str] = None
    has_navidrome_password: bool = False
    default_playlist_size: int = 20
    default_bpm_jitter: float = 5.0


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
    """Request to test Navidrome connection.

    Password is optional - if not provided, the stored password from config will be used.
    """

    url: str
    username: str
    password: Optional[str] = None


class TestNavidromeResponse(BaseModel):
    """Response for Navidrome connection test."""

    success: bool
    message: str


class UpdateConfigRequest(BaseModel):
    """Request to update configuration.

    All fields are optional - only provided fields will be updated.
    """

    music_library: Optional[str] = None
    navidrome_url: Optional[str] = None
    navidrome_username: Optional[str] = None
    navidrome_password: Optional[str] = None
    default_playlist_size: Optional[int] = None
    default_bpm_jitter: Optional[float] = None


class UpdateConfigResponse(BaseModel):
    """Response for configuration update."""

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
        default_playlist_size=config.default_playlist_size,
        default_bpm_jitter=config.default_bpm_jitter,
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
    config: Config = Depends(get_config),
) -> TestNavidromeResponse:
    """Test connection to Navidrome server.

    Attempts to authenticate with the provided credentials.
    If password is not provided, uses the stored password from config.

    :param request: Navidrome connection test request
    :param config: Application configuration for fallback password
    :return: Connection test result
    """
    from vibe_dj.services.navidrome_client import NavidromeClient

    try:
        safe_url = validate_outbound_url(request.url)
    except UnsafeOutboundURLError as e:
        return TestNavidromeResponse(success=False, message=str(e))

    # Use provided password, or fall back to stored password
    password = request.password if request.password else config.navidrome_password

    if not password:
        return TestNavidromeResponse(
            success=False,
            message="No password provided and no password stored in configuration",
        )

    try:
        client = NavidromeClient(
            base_url=safe_url,
            username=request.username,
            password=password,
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


@router.put("/config", response_model=UpdateConfigResponse)
def update_config(
    request: UpdateConfigRequest,
    config: Config = Depends(get_config),
) -> UpdateConfigResponse:
    """Update application configuration.

    Only provided fields will be updated. Existing values are preserved
    for fields not included in the request.

    For music_library, the path must be valid (exists and is a directory).
    For navidrome_password, if not provided, the existing password is preserved.

    :param request: Configuration update request
    :param config: Current application configuration
    :return: Update result
    """
    try:
        # Load existing config file to preserve all fields
        existing_data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r") as f:
                existing_data = json.load(f)

        # Validate music_library if provided
        if request.music_library is not None:
            path = request.music_library.strip()
            if path:
                if not os.path.exists(path):
                    return UpdateConfigResponse(
                        success=False,
                        message=f"Path does not exist: {path}",
                    )
                if not os.path.isdir(path):
                    return UpdateConfigResponse(
                        success=False,
                        message=f"Path is not a directory: {path}",
                    )
            existing_data["music_library"] = path

        # Update navidrome fields if provided
        if request.navidrome_url is not None:
            existing_data["navidrome_url"] = request.navidrome_url or None

        if request.navidrome_username is not None:
            existing_data["navidrome_username"] = request.navidrome_username or None

        # Only update password if explicitly provided (non-empty)
        # This preserves existing password when user doesn't change it
        if request.navidrome_password is not None and request.navidrome_password:
            existing_data["navidrome_password"] = request.navidrome_password

        # Validate and update playlist defaults
        if request.default_playlist_size is not None:
            if request.default_playlist_size not in ALLOWED_PLAYLIST_SIZES:
                return UpdateConfigResponse(
                    success=False,
                    message=f"default_playlist_size must be one of {ALLOWED_PLAYLIST_SIZES}, "
                    f"got {request.default_playlist_size}",
                )
            existing_data["default_playlist_size"] = request.default_playlist_size

        if request.default_bpm_jitter is not None:
            if not (BPM_JITTER_MIN <= request.default_bpm_jitter <= BPM_JITTER_MAX):
                return UpdateConfigResponse(
                    success=False,
                    message=f"default_bpm_jitter must be between {BPM_JITTER_MIN} and "
                    f"{BPM_JITTER_MAX}, got {request.default_bpm_jitter}",
                )
            existing_data["default_bpm_jitter"] = request.default_bpm_jitter

        # Write updated config to file
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(existing_data, f, indent=2)

        # Invalidate the config cache so next request gets fresh values
        invalidate_config_cache()

        logger.info("Configuration updated successfully")
        return UpdateConfigResponse(
            success=True,
            message="Configuration saved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return UpdateConfigResponse(
            success=False,
            message=f"Failed to save configuration: {str(e)}",
        )
