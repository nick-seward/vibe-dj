from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from vibe_dj.api.dependencies import (
    get_active_profile,
    get_config,
    get_navidrome_sync_service,
    get_playlist_generator,
    get_profile_database,
)
from vibe_dj.api.models import (
    PlaylistRequest,
    PlaylistResponse,
    SongResponse,
    SyncToNavidromeRequest,
)
from vibe_dj.core import MusicDatabase
from vibe_dj.models import Config, Playlist
from vibe_dj.models.profile import Profile
from vibe_dj.services import NavidromeSyncService, PlaylistGenerator

router = APIRouter(prefix="/api", tags=["playlist"])


def _song_to_response(song) -> SongResponse:
    """Convert a Song model to SongResponse.

    :param song: Song object
    :return: SongResponse object
    """
    return SongResponse(
        id=song.id,
        file_path=song.file_path,
        title=song.title,
        artist=song.artist,
        album=song.album,
        genre=song.genre,
        duration=song.duration,
        last_modified=song.last_modified,
    )


def playlist_to_response(playlist: Playlist) -> PlaylistResponse:
    """Convert Playlist model to API response.

    :param playlist: Playlist object
    :return: PlaylistResponse object
    """
    return PlaylistResponse(
        songs=[_song_to_response(song) for song in playlist.songs],
        seed_songs=[_song_to_response(song) for song in playlist.seed_songs],
        created_at=playlist.created_at,
        length=len(playlist.songs),
    )


@router.post("/playlist", response_model=PlaylistResponse)
def generate_playlist(
    request: PlaylistRequest,
    generator: PlaylistGenerator = Depends(get_playlist_generator),
    sync_service: NavidromeSyncService = Depends(get_navidrome_sync_service),
    config: Config = Depends(get_config),
    active_profile: Optional[Profile] = Depends(get_active_profile),
    profile_db=Depends(get_profile_database),
) -> PlaylistResponse:
    """Generate a playlist from seed songs.

    Creates a playlist based on audio similarity to the provided seed songs.
    Optionally syncs to Navidrome server.

    :param request: Playlist generation request
    :param generator: Playlist generator service
    :param sync_service: Navidrome sync service
    :param config: Application configuration
    :param active_profile: Active profile from X-Active-Profile header
    :return: Generated playlist with songs
    :raises HTTPException: If playlist generation fails
    """
    try:
        seeds = [seed.model_dump() for seed in request.seeds]

        playlist = generator.generate(
            seeds,
            length=request.length,
            bpm_jitter_percent=request.bpm_jitter,
        )

        if not playlist:
            raise HTTPException(
                status_code=400,
                detail="Could not generate playlist. Check that seed songs exist in the database.",
            )

        if request.sync_to_navidrome:
            nav_config = request.navidrome_config or {}
            profile_url = active_profile.subsonic_url if active_profile else None
            profile_username = (
                active_profile.subsonic_username if active_profile else None
            )
            profile_password_encrypted = (
                active_profile.subsonic_password_encrypted if active_profile else None
            )
            profile_password = (
                profile_db.decrypt_password(profile_password_encrypted)
                if profile_password_encrypted
                else None
            )
            result = sync_service.sync_playlist(
                playlist,
                nav_config.get("playlist_name"),
                nav_config.get("url") or profile_url,
                nav_config.get("username") or profile_username,
                nav_config.get("password") or profile_password,
            )

            if not result["success"]:
                logger.warning(f"Navidrome sync failed: {result.get('error')}")

        return playlist_to_response(playlist)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Playlist generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Playlist generation failed: {str(e)}"
        )


@router.post("/playlist/sync")
def sync_playlist_to_navidrome(
    request: SyncToNavidromeRequest,
    sync_service: NavidromeSyncService = Depends(get_navidrome_sync_service),
    config: Config = Depends(get_config),
    active_profile: Optional[Profile] = Depends(get_active_profile),
    profile_db=Depends(get_profile_database),
) -> dict:
    """Sync an existing playlist to Navidrome by song IDs.

    This endpoint syncs songs that have already been selected/generated,
    rather than generating a new playlist.

    :param request: Sync request with song IDs and Navidrome config
    :param sync_service: Navidrome sync service
    :param config: Application configuration
    :param active_profile: Active profile from X-Active-Profile header
    :return: Sync result with success status
    :raises HTTPException: If sync fails
    """
    try:
        with MusicDatabase(config) as db:
            songs = []
            for song_id in request.song_ids:
                song = db.get_song(song_id)
                if not song:
                    raise HTTPException(
                        status_code=404, detail=f"Song with ID {song_id} not found"
                    )
                songs.append(song)

            playlist = Playlist(songs=songs)

            nav_config = request.navidrome_config or {}
            profile_url = active_profile.subsonic_url if active_profile else None
            profile_username = (
                active_profile.subsonic_username if active_profile else None
            )
            profile_password_encrypted = (
                active_profile.subsonic_password_encrypted if active_profile else None
            )
            profile_password = (
                profile_db.decrypt_password(profile_password_encrypted)
                if profile_password_encrypted
                else None
            )
            result = sync_service.sync_playlist(
                playlist,
                nav_config.get("playlist_name", "Vibe DJ Playlist"),
                nav_config.get("url") or profile_url,
                nav_config.get("username") or profile_username,
                nav_config.get("password") or profile_password,
            )

            if not result["success"]:
                raise HTTPException(
                    status_code=400, detail=result.get("error", "Navidrome sync failed")
                )

            return {
                "success": True,
                "playlist_name": result.get("playlist_name"),
                "playlist_id": result.get("playlist_id"),
                "matched_count": result.get("matched_count"),
                "total_count": result.get("total_count"),
                "action": result.get("action"),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Navidrome sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
