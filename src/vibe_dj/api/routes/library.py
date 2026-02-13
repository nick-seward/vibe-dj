from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from vibe_dj.api.dependencies import get_db
from vibe_dj.api.models import LibraryStatsResponse
from vibe_dj.core import MusicDatabase

router = APIRouter(prefix="/api", tags=["library"])


@router.get("/library/stats", response_model=LibraryStatsResponse)
def get_library_stats(
    db: MusicDatabase = Depends(get_db),
) -> LibraryStatsResponse:
    """Get music library statistics.

    Returns comprehensive statistics about the indexed music library
    including song counts, artist/album counts, total play time,
    indexing completeness, and last indexed timestamp.

    :param db: Database connection
    :return: Library statistics
    """
    try:
        stats = db.get_library_stats()
        return LibraryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get library stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get library stats: {str(e)}"
        )
