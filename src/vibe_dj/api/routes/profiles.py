"""Profile management API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from vibe_dj.api.dependencies import get_profile_database
from vibe_dj.core.profile_database import ProfileDatabase

router = APIRouter(prefix="/api", tags=["profiles"])


class ProfileResponse(BaseModel):
    """Profile response model.

    Returns profile data without the encrypted password.
    """

    id: int
    display_name: str
    subsonic_url: Optional[str] = None
    subsonic_username: Optional[str] = None
    has_subsonic_password: bool = False
    created_at: str
    updated_at: str


class CreateProfileRequest(BaseModel):
    """Request to create a new profile."""

    display_name: str
    subsonic_url: Optional[str] = None
    subsonic_username: Optional[str] = None
    subsonic_password: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Request to update an existing profile.

    All fields are optional - only provided fields will be updated.
    """

    display_name: Optional[str] = None
    subsonic_url: Optional[str] = None
    subsonic_username: Optional[str] = None
    subsonic_password: Optional[str] = None


def _profile_to_response(profile) -> ProfileResponse:
    """Convert a Profile ORM object to a ProfileResponse.

    :param profile: Profile ORM object
    :return: ProfileResponse with formatted fields
    """
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        subsonic_url=profile.subsonic_url,
        subsonic_username=profile.subsonic_username,
        has_subsonic_password=bool(profile.subsonic_password_encrypted),
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.get("/profiles", response_model=List[ProfileResponse])
def list_profiles(
    profile_db: ProfileDatabase = Depends(get_profile_database),
) -> List[ProfileResponse]:
    """List all profiles.

    :param profile_db: Profile database instance
    :return: List of all profiles
    """
    try:
        profiles = profile_db.get_all_profiles()
        return [_profile_to_response(p) for p in profiles]
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list profiles: {str(e)}"
        )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    profile_db: ProfileDatabase = Depends(get_profile_database),
) -> ProfileResponse:
    """Get a specific profile by ID.

    :param profile_id: Profile identifier
    :param profile_db: Profile database instance
    :return: Profile details
    :raises HTTPException: If profile not found
    """
    try:
        profile = profile_db.get_profile(profile_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile with ID {profile_id} not found"
            )
        return _profile_to_response(profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.post("/profiles", response_model=ProfileResponse, status_code=201)
def create_profile(
    request: CreateProfileRequest,
    profile_db: ProfileDatabase = Depends(get_profile_database),
) -> ProfileResponse:
    """Create a new profile.

    :param request: Profile creation request
    :param profile_db: Profile database instance
    :return: Created profile
    :raises HTTPException: If display name already exists
    """
    try:
        profile = profile_db.create_profile(
            display_name=request.display_name,
            subsonic_url=request.subsonic_url,
            subsonic_username=request.subsonic_username,
            subsonic_password=request.subsonic_password,
        )
        return _profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create profile: {str(e)}"
        )


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    request: UpdateProfileRequest,
    profile_db: ProfileDatabase = Depends(get_profile_database),
) -> ProfileResponse:
    """Update an existing profile.

    Only provided fields will be updated.

    :param profile_id: Profile identifier
    :param request: Profile update request
    :param profile_db: Profile database instance
    :return: Updated profile
    :raises HTTPException: If profile not found or name conflict
    """
    try:
        profile = profile_db.update_profile(
            profile_id=profile_id,
            display_name=request.display_name,
            subsonic_url=request.subsonic_url,
            subsonic_username=request.subsonic_username,
            subsonic_password=request.subsonic_password,
        )
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile with ID {profile_id} not found"
            )
        return _profile_to_response(profile)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(
    profile_id: int,
    profile_db: ProfileDatabase = Depends(get_profile_database),
) -> None:
    """Delete a profile.

    The 'Shared' profile cannot be deleted.

    :param profile_id: Profile identifier
    :param profile_db: Profile database instance
    :raises HTTPException: If profile not found or is the Shared profile
    """
    try:
        deleted = profile_db.delete_profile(profile_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Profile with ID {profile_id} not found"
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete profile: {str(e)}"
        )
