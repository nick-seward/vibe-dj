from .config import router as config_router
from .index import router as index_router
from .library import router as library_router
from .playlist import router as playlist_router
from .profiles import router as profiles_router
from .songs import router as songs_router

__all__ = [
    "config_router",
    "index_router",
    "library_router",
    "playlist_router",
    "profiles_router",
    "songs_router",
]
