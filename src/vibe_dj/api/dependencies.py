import os
from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, UploadFile
from loguru import logger

from vibe_dj.api.background import JobManager, job_manager
from vibe_dj.core import AudioAnalyzer, LibraryIndexer, MusicDatabase, SimilarityIndex
from vibe_dj.core.profile_database import ProfileDatabase
from vibe_dj.models import Config
from vibe_dj.models.profile import Profile
from vibe_dj.services import NavidromeSyncService, PlaylistGenerator

_config_cache: Optional[Config] = None


def invalidate_config_cache() -> None:
    """Invalidate the cached configuration.

    Call this after updating the config file to ensure
    subsequent requests get the fresh values.
    """
    global _config_cache
    _config_cache = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get application configuration.

    Loads configuration from file or defaults.
    Priority: config_path > config.json > defaults
    Uses simple caching to avoid reloading config on every request.

    :param config_path: Optional path to config file
    :return: Configuration object
    """
    global _config_cache

    # Return cached config if available and no specific path requested
    if _config_cache is not None and config_path is None:
        return _config_cache

    if config_path and os.path.exists(config_path):
        logger.info(f"Loading config from {config_path}")
        config = Config.from_file(config_path)
        _config_cache = config
        return config

    default_config_path = "config.json"
    if os.path.exists(default_config_path):
        logger.info(f"Loading config from {default_config_path}")
        config = Config.from_file(default_config_path)
        _config_cache = config
        return config

    logger.info("Using default configuration")
    config = Config()
    _config_cache = config
    return config


def get_db(
    config: Config = Depends(get_config),
) -> Generator[MusicDatabase, None, None]:
    """Provide database connection with context management.

    :param config: Application configuration
    :yield: MusicDatabase instance
    """
    with MusicDatabase(config) as db:
        yield db


_similarity_index_cache: Optional[SimilarityIndex] = None


def get_similarity_index(config: Config = Depends(get_config)) -> SimilarityIndex:
    """Provide FAISS similarity index (singleton).

    Loads the index once and caches it for reuse.

    :param config: Application configuration
    :return: SimilarityIndex instance
    :raises HTTPException: If index cannot be loaded
    """
    global _similarity_index_cache

    if _similarity_index_cache is not None:
        return _similarity_index_cache

    try:
        similarity_index = SimilarityIndex(config)
        if os.path.exists(config.faiss_index_path):
            similarity_index.load()
            logger.info(f"Loaded FAISS index from {config.faiss_index_path}")
        else:
            logger.warning(f"FAISS index not found at {config.faiss_index_path}")
        _similarity_index_cache = similarity_index
        return similarity_index
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        raise HTTPException(status_code=503, detail="Similarity index unavailable")


def get_audio_analyzer(config: Config = Depends(get_config)) -> AudioAnalyzer:
    """Provide audio analyzer instance.

    :param config: Application configuration
    :return: AudioAnalyzer instance
    """
    return AudioAnalyzer(config)


def get_playlist_generator(
    config: Config = Depends(get_config),
    db: MusicDatabase = Depends(get_db),
    similarity_index: SimilarityIndex = Depends(get_similarity_index),
) -> PlaylistGenerator:
    """Provide playlist generator service.

    :param config: Application configuration
    :param db: Database connection
    :param similarity_index: FAISS similarity index
    :return: PlaylistGenerator instance
    """
    return PlaylistGenerator(config, db, similarity_index)


def get_navidrome_sync_service(
    config: Config = Depends(get_config),
) -> NavidromeSyncService:
    """Provide Navidrome sync service.

    :param config: Application configuration
    :return: NavidromeSyncService instance
    """
    return NavidromeSyncService(config)


def get_library_indexer(
    config: Config = Depends(get_config),
    db: MusicDatabase = Depends(get_db),
    analyzer: AudioAnalyzer = Depends(get_audio_analyzer),
    similarity_index: SimilarityIndex = Depends(get_similarity_index),
) -> LibraryIndexer:
    """Provide library indexer service.

    :param config: Application configuration
    :param db: Database connection
    :param analyzer: Audio analyzer
    :param similarity_index: FAISS similarity index
    :return: LibraryIndexer instance
    """
    return LibraryIndexer(config, db, analyzer, similarity_index)


def get_job_manager() -> JobManager:
    """Provide job manager singleton.

    :return: JobManager instance
    """
    return job_manager


_profile_db_instance: Optional[ProfileDatabase] = None


def get_profile_database() -> Generator[ProfileDatabase, None, None]:
    """Provide profile database connection with context management.

    Uses a singleton ProfileDatabase instance with a separate session
    per request. The database file is stored alongside the main database.

    :yield: ProfileDatabase instance with active session
    """
    global _profile_db_instance

    if _profile_db_instance is None:
        db_path = os.environ.get("VIBE_DJ_PROFILES_DB", "profiles.db")
        encryption_key = os.environ.get("VIBE_DJ_ENCRYPTION_KEY")
        _profile_db_instance = ProfileDatabase(
            db_path=db_path, encryption_key=encryption_key
        )
        _profile_db_instance.connect()
        _profile_db_instance.init_db()

    yield _profile_db_instance


def get_active_profile(
    profile_db: ProfileDatabase = Depends(get_profile_database),
    x_active_profile: Optional[str] = Header(None),
) -> Optional[Profile]:
    """Get the active profile from the X-Active-Profile header.

    Resolves the profile ID from the request header and returns
    the corresponding Profile object. Returns None if no header
    is provided.

    :param profile_db: Profile database instance
    :param x_active_profile: Profile ID from request header
    :return: Active Profile object, or None if no header
    :raises HTTPException: If profile ID is invalid or not found
    """
    if not x_active_profile:
        return None

    try:
        profile_id = int(x_active_profile)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid X-Active-Profile header: '{x_active_profile}' is not a valid profile ID",
        )

    profile = profile_db.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile with ID {profile_id} not found",
        )
    return profile


async def parse_config_file(file: Optional[UploadFile] = None) -> Optional[Config]:
    """Parse uploaded configuration file.

    :param file: Uploaded config file
    :return: Config object if file provided, None otherwise
    """
    if not file:
        return None

    try:
        content = await file.read()
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp.write(content.decode("utf-8"))
            tmp_path = tmp.name

        config = Config.from_file(tmp_path)
        os.unlink(tmp_path)
        return config
    except Exception as e:
        logger.error(f"Failed to parse config file: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid config file: {str(e)}")
