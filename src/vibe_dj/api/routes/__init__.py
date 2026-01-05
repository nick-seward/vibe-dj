from .index import router as index_router
from .playlist import router as playlist_router
from .songs import router as songs_router

__all__ = ["index_router", "playlist_router", "songs_router"]
