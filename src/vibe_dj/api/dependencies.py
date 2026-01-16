import os
from typing import Generator, Optional

from fastapi import Depends, HTTPException, UploadFile
from loguru import logger

from vibe_dj.api.background import JobManager, job_manager
from vibe_dj.core import AudioAnalyzer, LibraryIndexer, MusicDatabase, SimilarityIndex
from vibe_dj.models import Config
from vibe_dj.services import NavidromeSyncService, PlaylistExporter, PlaylistGenerator

_config_cache: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get application configuration.

    Loads configuration from file, environment variables, or defaults.
    Priority: config_path > env vars > config.json > defaults
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

    env_config_path = os.getenv("VIBE_DJ_CONFIG_PATH")
    if env_config_path and os.path.exists(env_config_path):
        logger.info(f"Loading config from env: {env_config_path}")
        config = Config.from_file(env_config_path)
        _config_cache = config
        return config

    default_config_path = "config.json"
    if os.path.exists(default_config_path):
        logger.info(f"Loading config from {default_config_path}")
        config = Config.from_file(default_config_path)
        _config_cache = config
        return config

    config_dict = {}

    if music_library := os.getenv("MUSIC_LIBRARY"):
        config_dict["music_library"] = music_library
    if db_path := os.getenv("VIBE_DJ_DATABASE_PATH"):
        config_dict["database_path"] = db_path
    if faiss_path := os.getenv("VIBE_DJ_FAISS_INDEX_PATH"):
        config_dict["faiss_index_path"] = faiss_path
    if navidrome_url := os.getenv("NAVIDROME_URL"):
        config_dict["navidrome_url"] = navidrome_url
    if navidrome_username := os.getenv("NAVIDROME_USERNAME"):
        config_dict["navidrome_username"] = navidrome_username
    if navidrome_password := os.getenv("NAVIDROME_PASSWORD"):
        config_dict["navidrome_password"] = navidrome_password

    if config_dict:
        logger.info("Loading config from environment variables")
        config = Config.from_dict(config_dict)
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


def get_playlist_exporter(config: Config = Depends(get_config)) -> PlaylistExporter:
    """Provide playlist exporter service.

    :param config: Application configuration
    :return: PlaylistExporter instance
    """
    return PlaylistExporter(config)


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
