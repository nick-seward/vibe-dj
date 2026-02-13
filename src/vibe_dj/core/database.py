from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, create_engine, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from vibe_dj.models import Base, Config, Features, Song


class MusicDatabase:
    """Database interface for managing music library data.

    Provides methods for storing and retrieving songs, features, and
    managing the SQLAlchemy session. Supports context manager
    protocol for automatic connection management.
    """

    def __init__(self, config: Config):
        """Initialize the database with configuration.

        :param config: Configuration object containing database path
        """
        self.config = config
        self._engine = create_engine(f"sqlite:///{config.database_path}")
        self._session_factory = sessionmaker(bind=self._engine)
        self._session: Optional[Session] = None

    def __enter__(self) -> "MusicDatabase":
        """Enter context manager, establishing database session.

        :return: Self reference for use in with statement
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, closing database session.

        :param exc_type: Exception type if an exception occurred
        :param exc_val: Exception value if an exception occurred
        :param exc_tb: Exception traceback if an exception occurred
        """
        self.close()

    def connect(self) -> None:
        """Establish a new SQLAlchemy session.

        Creates a new session if one doesn't exist.
        """
        if self._session is None:
            self._session = self._session_factory()

    def close(self) -> None:
        """Close the database session if open."""
        if self._session:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        """Get the active database session.

        :return: Active SQLAlchemy session
        :raises RuntimeError: If database is not connected
        """
        if self._session is None:
            raise RuntimeError(
                "Database not connected. Use context manager or call connect()."
            )
        return self._session

    @property
    def connection(self) -> Session:
        """Get the active database session (alias for backward compatibility).

        :return: Active SQLAlchemy session
        :raises RuntimeError: If database is not connected
        """
        return self.session

    def init_db(self) -> None:
        """Initialize database schema.

        Creates the songs and features tables if they don't exist.
        """
        Base.metadata.create_all(self._engine)

    def add_song(self, song: Song, features: Optional[Features] = None) -> int:
        """Add or update a song and optionally its features.

        :param song: Song object to add or update
        :param features: Optional Features object to associate with the song
        :return: ID of the inserted or updated song
        """
        existing = self.session.execute(
            select(Song).where(Song.file_path == song.file_path)
        ).scalar_one_or_none()

        if existing:
            existing.title = song.title
            existing.artist = song.artist
            existing.album = song.album
            existing.genre = song.genre
            existing.last_modified = song.last_modified
            existing.duration = song.duration
            merged_song = existing
        else:
            self.session.add(song)
            self.session.flush()
            merged_song = song

        if features:
            features.song_id = merged_song.id
            existing_features = self.session.get(Features, merged_song.id)
            if existing_features:
                existing_features._feature_vector_bytes = features._feature_vector_bytes
                existing_features.bpm = features.bpm
            else:
                self.session.add(features)

        self.session.commit()
        return merged_song.id

    def get_song(self, song_id: int) -> Optional[Song]:
        """Retrieve a song by its ID.

        :param song_id: ID of the song to retrieve
        :return: Song object if found, None otherwise
        """
        return self.session.get(Song, song_id)

    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Retrieve a song by its file path.

        :param file_path: File path of the song to retrieve
        :return: Song object if found, None otherwise
        """
        return self.session.execute(
            select(Song).where(Song.file_path == file_path)
        ).scalar_one_or_none()

    def find_songs_by_title(self, title: str) -> List[Song]:
        """Find songs with titles matching a search pattern.

        :param title: Title search string (supports partial matches)
        :return: List of matching Song objects
        """
        return list(
            self.session.execute(select(Song).where(Song.title.like(f"%{title}%")))
            .scalars()
            .all()
        )

    def find_song_exact(self, title: str, artist: str, album: str) -> Optional[Song]:
        """Find a song by exact title, artist, and album match.

        :param title: Exact title of the song
        :param artist: Exact artist name
        :param album: Exact album name
        :return: Song object if found, None otherwise
        """
        return self.session.execute(
            select(Song).where(
                Song.title == title,
                Song.artist == artist,
                Song.album == album,
            )
        ).scalar_one_or_none()

    def get_features(self, song_id: int) -> Optional[Features]:
        """Retrieve features for a specific song.

        :param song_id: ID of the song
        :return: Features object if found, None otherwise
        """
        return self.session.get(Features, song_id)

    def get_song_with_features(self, song_id: int) -> Optional[Tuple[Song, Features]]:
        """Retrieve a song and its features together.

        :param song_id: ID of the song
        :return: Tuple of (Song, Features) if found, None otherwise
        """
        song = self.session.get(Song, song_id)
        if song and song.features:
            return (song, song.features)
        return None

    def get_all_songs_with_features(self) -> List[Tuple[Song, Features]]:
        """Retrieve all songs that have features.

        :return: List of (Song, Features) tuples ordered by song ID
        """
        songs = (
            self.session.execute(select(Song).join(Features).order_by(Song.id))
            .scalars()
            .all()
        )

        return [(song, song.features) for song in songs if song.features]

    def get_all_file_paths_with_mtime(self) -> Dict[str, float]:
        """Get all file paths and their last modified times.

        :return: Dictionary mapping file paths to modification timestamps
        """
        results = self.session.execute(select(Song.file_path, Song.last_modified)).all()
        return {row[0]: row[1] for row in results}

    def delete_song(self, file_path: str) -> bool:
        """Delete a song by its file path.

        :param file_path: File path of the song to delete
        :return: True if a song was deleted, False otherwise
        """
        song = self.session.execute(
            select(Song).where(Song.file_path == file_path)
        ).scalar_one_or_none()

        if song:
            self.session.delete(song)
            self.session.commit()
            return True
        return False

    def get_songs_by_ids(self, song_ids: List[int]) -> List[Song]:
        """Retrieve multiple songs by their IDs.

        :param song_ids: List of song IDs to retrieve
        :return: List of Song objects for the given IDs
        """
        if not song_ids:
            return []

        return list(
            self.session.execute(select(Song).where(Song.id.in_(song_ids)))
            .scalars()
            .all()
        )

    def commit(self) -> None:
        """Commit pending database transactions."""
        self.session.commit()

    def get_songs_without_features(
        self, file_paths: Optional[List[str]] = None
    ) -> List[Song]:
        """Get songs that exist in DB but don't have features yet.

        :param file_paths: Optional list of file paths to filter by
        :return: List of Song objects without associated features
        """
        stmt = select(Song).outerjoin(Features).where(Features.song_id.is_(None))

        if file_paths:
            stmt = stmt.where(Song.file_path.in_(file_paths))

        return list(self.session.execute(stmt).scalars().all())

    def get_indexing_stats(self) -> Dict[str, int]:
        """Get statistics about indexing progress.

        :return: Dictionary with keys 'total_songs', 'songs_with_features',
                 and 'songs_without_features'
        """
        total_songs = (
            self.session.execute(select(func.count()).select_from(Song)).scalar() or 0
        )

        songs_with_features = (
            self.session.execute(select(func.count()).select_from(Features)).scalar()
            or 0
        )

        songs_without_features = total_songs - songs_with_features

        return {
            "total_songs": total_songs,
            "songs_with_features": songs_with_features,
            "songs_without_features": songs_without_features,
        }

    def get_all_songs(self, limit: int = 100, offset: int = 0) -> List[Song]:
        """Retrieve all songs with pagination.

        :param limit: Maximum number of songs to return
        :param offset: Number of songs to skip
        :return: List of Song objects
        """
        return list(
            self.session.execute(
                select(Song).order_by(Song.id).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )

    def search_songs(self, query: str, limit: int = 100, offset: int = 0) -> List[Song]:
        """Search songs by title, artist, or album.

        :param query: Search query string
        :param limit: Maximum number of songs to return
        :param offset: Number of songs to skip
        :return: List of matching Song objects
        """
        search_pattern = f"%{query}%"
        return list(
            self.session.execute(
                select(Song)
                .where(
                    or_(
                        Song.title.like(search_pattern),
                        Song.artist.like(search_pattern),
                        Song.album.like(search_pattern),
                    )
                )
                .order_by(Song.id)
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

    def count_songs(self, search: Optional[str] = None) -> int:
        """Count total songs, optionally filtered by search query.

        :param search: Optional search query string
        :return: Total count of songs
        """
        if search:
            search_pattern = f"%{search}%"
            stmt = (
                select(func.count())
                .select_from(Song)
                .where(
                    or_(
                        Song.title.like(search_pattern),
                        Song.artist.like(search_pattern),
                        Song.album.like(search_pattern),
                    )
                )
            )
        else:
            stmt = select(func.count()).select_from(Song)

        return self.session.execute(stmt).scalar() or 0

    def search_songs_multi(
        self,
        artist: Optional[str] = None,
        title: Optional[str] = None,
        album: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Song]:
        """Search songs with separate artist, title, and album filters.

        All provided filters are combined with AND logic.

        :param artist: Optional artist name filter
        :param title: Optional song title filter
        :param album: Optional album name filter
        :param limit: Maximum number of songs to return
        :param offset: Number of songs to skip
        :return: List of matching Song objects
        """
        conditions = []
        if artist:
            conditions.append(Song.artist.ilike(f"%{artist}%"))
        if title:
            conditions.append(Song.title.ilike(f"%{title}%"))
        if album:
            conditions.append(Song.album.ilike(f"%{album}%"))

        stmt = select(Song)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        return list(
            self.session.execute(
                stmt.order_by(Song.artist, Song.album, Song.title)
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

    def get_library_stats(self) -> Dict[str, object]:
        """Get comprehensive library statistics.

        :return: Dictionary with keys 'total_songs', 'artist_count',
                 'album_count', 'total_duration', 'songs_with_features',
                 and 'last_indexed'
        """
        total_songs = (
            self.session.execute(select(func.count()).select_from(Song)).scalar() or 0
        )

        artist_count = (
            self.session.execute(
                select(func.count(func.distinct(Song.artist)))
            ).scalar()
            or 0
        )

        album_count = (
            self.session.execute(
                select(func.count(func.distinct(Song.album)))
            ).scalar()
            or 0
        )

        total_duration = (
            self.session.execute(select(func.sum(Song.duration))).scalar() or 0
        )

        songs_with_features = (
            self.session.execute(select(func.count()).select_from(Features)).scalar()
            or 0
        )

        last_indexed = self.session.execute(
            select(func.max(Song.last_modified))
        ).scalar()

        return {
            "total_songs": total_songs,
            "artist_count": artist_count,
            "album_count": album_count,
            "total_duration": total_duration,
            "songs_with_features": songs_with_features,
            "last_indexed": last_indexed,
        }

    def count_songs_multi(
        self,
        artist: Optional[str] = None,
        title: Optional[str] = None,
        album: Optional[str] = None,
    ) -> int:
        """Count songs matching the multi-field search criteria.

        :param artist: Optional artist name filter
        :param title: Optional song title filter
        :param album: Optional album name filter
        :return: Total count of matching songs
        """
        conditions = []
        if artist:
            conditions.append(Song.artist.ilike(f"%{artist}%"))
        if title:
            conditions.append(Song.title.ilike(f"%{title}%"))
        if album:
            conditions.append(Song.album.ilike(f"%{album}%"))

        stmt = select(func.count()).select_from(Song)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        return self.session.execute(stmt).scalar() or 0
