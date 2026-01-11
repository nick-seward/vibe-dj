from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from ...core import MusicDatabase
from ..dependencies import get_db
from ..models import FeaturesResponse, SongDetailResponse, SongResponse, SongsListResponse

router = APIRouter(prefix="/api", tags=["songs"])


@router.get("/songs", response_model=SongsListResponse)
def list_songs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of songs to return"),
    offset: int = Query(0, ge=0, description="Number of songs to skip"),
    search: Optional[str] = Query(None, description="Search query for title, artist, or album"),
    db: MusicDatabase = Depends(get_db),
) -> SongsListResponse:
    """List songs with pagination and optional search.
    
    Returns a paginated list of songs from the database. Optionally filter
    by search query matching title, artist, or album.
    
    :param limit: Maximum number of songs to return
    :param offset: Number of songs to skip for pagination
    :param search: Optional search query
    :param db: Database connection
    :return: Paginated list of songs
    """
    try:
        if search:
            songs = db.search_songs(search, limit=limit, offset=offset)
            total = db.count_songs(search=search)
        else:
            songs = db.get_all_songs(limit=limit, offset=offset)
            total = db.count_songs()
        
        return SongsListResponse(
            songs=[
                SongResponse(
                    id=song.id,
                    file_path=song.file_path,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    genre=song.genre,
                    duration=song.duration,
                    last_modified=song.last_modified,
                )
                for song in songs
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Failed to list songs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list songs: {str(e)}")


@router.get("/songs/search", response_model=SongsListResponse)
def search_songs_multi(
    artist: Optional[str] = Query(None, description="Artist name to search for"),
    title: Optional[str] = Query(None, description="Song title to search for"),
    album: Optional[str] = Query(None, description="Album name to search for"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of songs to return (max 200)"),
    offset: int = Query(0, ge=0, description="Number of songs to skip"),
    db: MusicDatabase = Depends(get_db),
) -> SongsListResponse:
    """Search songs with separate artist, title, and album filters.
    
    Returns songs matching all provided filters. At least one filter must be specified.
    The maximum depth into search results is 1000 (offset + limit <= 1000).
    
    :param artist: Optional artist name filter
    :param title: Optional song title filter
    :param album: Optional album name filter
    :param limit: Maximum number of songs to return (max 200 per page)
    :param offset: Number of songs to skip for pagination
    :param db: Database connection
    :return: Paginated list of matching songs
    """
    if not artist and not title and not album:
        raise HTTPException(
            status_code=400,
            detail="At least one search parameter (artist, title, or album) is required"
        )
    
    if offset + limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maximum search depth is 1000 results (offset + limit cannot exceed 1000)"
        )
    
    try:
        songs = db.search_songs_multi(
            artist=artist,
            title=title,
            album=album,
            limit=limit,
            offset=offset,
        )
        total = db.count_songs_multi(artist=artist, title=title, album=album)
        
        return SongsListResponse(
            songs=[
                SongResponse(
                    id=song.id,
                    file_path=song.file_path,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    genre=song.genre,
                    duration=song.duration,
                    last_modified=song.last_modified,
                )
                for song in songs
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search songs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search songs: {str(e)}")


@router.get("/songs/{song_id}", response_model=SongDetailResponse)
def get_song(
    song_id: int,
    db: MusicDatabase = Depends(get_db),
) -> SongDetailResponse:
    """Get detailed information about a specific song.
    
    Returns song metadata and audio features if available.
    
    :param song_id: Song identifier
    :param db: Database connection
    :return: Detailed song information
    :raises HTTPException: If song not found
    """
    try:
        song = db.get_song(song_id)
        
        if not song:
            raise HTTPException(status_code=404, detail=f"Song with ID {song_id} not found")
        
        song_response = SongResponse(
            id=song.id,
            file_path=song.file_path,
            title=song.title,
            artist=song.artist,
            album=song.album,
            genre=song.genre,
            duration=song.duration,
            last_modified=song.last_modified,
        )
        
        features = db.get_features(song_id)
        features_response = None
        
        if features:
            features_response = FeaturesResponse(
                song_id=features.song_id,
                bpm=features.bpm,
                feature_vector_length=len(features.feature_vector),
            )
        
        return SongDetailResponse(
            song=song_response,
            features=features_response,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get song {song_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get song: {str(e)}")
