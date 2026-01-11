import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from ...models import Config, Playlist
from ...services import NavidromeSyncService, PlaylistExporter, PlaylistGenerator
from ..dependencies import (
    get_config,
    get_navidrome_sync_service,
    get_playlist_exporter,
    get_playlist_generator,
)
from ..models import (
    ExportRequest,
    PlaylistRequest,
    PlaylistResponse,
    SongResponse,
    SyncToNavidromeRequest,
)

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
    exporter: PlaylistExporter = Depends(get_playlist_exporter),
    sync_service: NavidromeSyncService = Depends(get_navidrome_sync_service),
    config: Config = Depends(get_config),
) -> PlaylistResponse:
    """Generate a playlist from seed songs.

    Creates a playlist based on audio similarity to the provided seed songs.
    Optionally syncs to Navidrome server.

    :param request: Playlist generation request
    :param generator: Playlist generator service
    :param exporter: Playlist exporter service
    :param sync_service: Navidrome sync service
    :param config: Application configuration
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

        if request.format in ["m3u", "m3u8"]:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f".{request.format}", delete=False
            ) as tmp:
                tmp_path = tmp.name

            try:
                exporter.export(playlist, tmp_path, output_format=request.format)

                if request.sync_to_navidrome:
                    nav_config = request.navidrome_config or {}
                    result = sync_service.sync_playlist(
                        playlist,
                        tmp_path,
                        nav_config.get("playlist_name"),
                        nav_config.get("url"),
                        nav_config.get("username"),
                        nav_config.get("password"),
                    )

                    if not result["success"]:
                        logger.warning(f"Navidrome sync failed: {result.get('error')}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

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


@router.post("/playlist/download")
def generate_and_download_playlist(
    request: PlaylistRequest,
    generator: PlaylistGenerator = Depends(get_playlist_generator),
    exporter: PlaylistExporter = Depends(get_playlist_exporter),
) -> FileResponse:
    """Generate a playlist and download as a file.

    Creates a playlist and returns it as a downloadable file in the requested format.

    :param request: Playlist generation request
    :param generator: Playlist generator service
    :param exporter: Playlist exporter service
    :return: File download response
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

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{request.format}", delete=False
        ) as tmp:
            tmp_path = tmp.name

        exporter.export(playlist, tmp_path, output_format=request.format)

        media_type_map = {
            "m3u": "audio/x-mpegurl",
            "m3u8": "audio/x-mpegurl",
            "json": "application/json",
        }

        return FileResponse(
            path=tmp_path,
            media_type=media_type_map.get(request.format, "application/octet-stream"),
            filename=f"playlist.{request.format}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Playlist generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Playlist generation failed: {str(e)}"
        )


@router.post("/export")
def export_playlist(
    request: ExportRequest,
    exporter: PlaylistExporter = Depends(get_playlist_exporter),
    config: Config = Depends(get_config),
) -> dict:
    """Export a list of songs to a playlist file.

    Creates a playlist file from the provided song IDs.

    :param request: Export request with song IDs and format
    :param exporter: Playlist exporter service
    :param config: Application configuration
    :return: Success message with output path
    :raises HTTPException: If export fails
    """
    try:
        from ...core import MusicDatabase
        from ...models import Playlist as PlaylistModel

        with MusicDatabase(config) as db:
            songs = []
            for song_id in request.song_ids:
                song = db.get_song(song_id)
                if not song:
                    raise HTTPException(
                        status_code=404, detail=f"Song with ID {song_id} not found"
                    )
                songs.append(song)

            playlist = PlaylistModel(songs=songs)
            exporter.export(playlist, request.output_path, output_format=request.format)

            return {
                "success": True,
                "message": f"Playlist exported to {request.output_path}",
                "song_count": len(songs),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/playlist/sync")
def sync_playlist_to_navidrome(
    request: SyncToNavidromeRequest,
    sync_service: NavidromeSyncService = Depends(get_navidrome_sync_service),
    config: Config = Depends(get_config),
) -> dict:
    """Sync an existing playlist to Navidrome by song IDs.

    This endpoint syncs songs that have already been selected/generated,
    rather than generating a new playlist.

    :param request: Sync request with song IDs and Navidrome config
    :param sync_service: Navidrome sync service
    :param config: Application configuration
    :return: Sync result with success status
    :raises HTTPException: If sync fails
    """
    try:
        from ...core import MusicDatabase
        from ...models import Playlist as PlaylistModel

        with MusicDatabase(config) as db:
            songs = []
            for song_id in request.song_ids:
                song = db.get_song(song_id)
                if not song:
                    raise HTTPException(
                        status_code=404, detail=f"Song with ID {song_id} not found"
                    )
                songs.append(song)

            playlist = PlaylistModel(songs=songs)

            nav_config = request.navidrome_config or {}
            result = sync_service.sync_playlist(
                playlist,
                "/tmp/sync_playlist.m3u",
                nav_config.get("playlist_name", "Vibe DJ Playlist"),
                nav_config.get("url"),
                nav_config.get("username"),
                nav_config.get("password"),
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
