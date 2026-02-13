from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SeedSong(BaseModel):
    """Seed song specification for playlist generation.

    Requires exact match on title, artist, and album for accurate
    song identification in the database.
    """

    title: str = Field(..., description="Song title")
    artist: str = Field(..., description="Artist name")
    album: str = Field(..., description="Album name")


class IndexRequest(BaseModel):
    """Request to index a music library.

    Triggers background indexing of audio files in the specified directory.
    """

    library_path: str = Field(..., description="Path to music library directory")
    config_overrides: Optional[Dict[str, Any]] = Field(
        None, description="Optional configuration overrides"
    )


class PlaylistRequest(BaseModel):
    """Request to generate a playlist from seed songs.

    Creates a playlist based on audio similarity to the provided seed songs.
    """

    seeds: List[SeedSong] = Field(
        ..., min_length=1, description="Seed songs for playlist generation"
    )
    length: int = Field(20, ge=1, le=1000, description="Number of songs in playlist")
    bpm_jitter: float = Field(
        5.0, ge=0.0, le=100.0, description="BPM jitter percentage for sorting"
    )
    format: Literal["m3u", "m3u8", "json"] = Field("json", description="Output format")
    sync_to_navidrome: bool = Field(
        False, description="Sync playlist to Navidrome server"
    )
    navidrome_config: Optional[Dict[str, str]] = Field(
        None,
        description="Navidrome configuration (url, username, password, playlist_name)",
    )


class ExportRequest(BaseModel):
    """Request to export a playlist to a file.

    Exports a list of songs to the specified format.
    """

    song_ids: List[int] = Field(
        ..., min_length=1, description="List of song IDs to export"
    )
    format: Literal["m3u", "m3u8", "json"] = Field("m3u", description="Export format")
    output_path: str = Field(..., description="Output file path")


class SyncToNavidromeRequest(BaseModel):
    """Request to sync an existing playlist to Navidrome.

    Syncs a list of songs by their IDs to Navidrome server.
    """

    song_ids: List[int] = Field(
        ..., min_length=1, description="List of song IDs to sync"
    )
    navidrome_config: Optional[Dict[str, str]] = Field(
        None,
        description="Navidrome configuration (url, username, password, playlist_name)",
    )


class SongResponse(BaseModel):
    """Song metadata response.

    Contains all metadata for a single song.
    """

    id: int
    file_path: str
    title: str
    artist: str
    album: str
    genre: str
    duration: Optional[int] = None
    last_modified: float


class FeaturesResponse(BaseModel):
    """Audio features response.

    Contains extracted audio features for a song.
    """

    song_id: int
    bpm: float
    feature_vector_length: int


class SongDetailResponse(BaseModel):
    """Detailed song response with features.

    Includes both metadata and audio features if available.
    """

    song: SongResponse
    features: Optional[FeaturesResponse] = None


class SongsListResponse(BaseModel):
    """Paginated list of songs.

    Contains songs with pagination metadata.
    """

    songs: List[SongResponse]
    total: int
    limit: int
    offset: int


class PlaylistResponse(BaseModel):
    """Generated playlist response.

    Contains the generated playlist with songs and metadata.
    """

    songs: List[SongResponse]
    seed_songs: List[SongResponse]
    created_at: datetime
    length: int


class IndexJobResponse(BaseModel):
    """Response for index job creation.

    Contains job ID and initial status for polling.
    """

    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str


class JobStatusResponse(BaseModel):
    """Job status response for polling.

    Contains current status, progress information, and any errors.
    """

    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ActiveJobResponse(BaseModel):
    """Response for active indexing job check.

    Returns the currently active job status, or null job_id with idle status
    if no job is active.
    """

    job_id: Optional[str] = None
    status: Literal["queued", "running", "idle"] = "idle"
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class LibraryStatsResponse(BaseModel):
    """Library statistics response.

    Contains comprehensive statistics about the indexed music library.
    """

    total_songs: int = Field(..., description="Total number of songs in the library")
    artist_count: int = Field(..., description="Number of distinct artists")
    album_count: int = Field(..., description="Number of distinct albums")
    total_duration: int = Field(
        ..., description="Total play time in seconds across all songs"
    )
    songs_with_features: int = Field(
        ..., description="Number of songs with extracted audio features"
    )
    last_indexed: Optional[float] = Field(
        None, description="Timestamp of the most recently indexed song"
    )


class HealthResponse(BaseModel):
    """Health check response.

    Indicates system health and component status.
    """

    status: Literal["ok", "degraded", "error"]
    database: str
    faiss_index: str
    message: Optional[str] = None
