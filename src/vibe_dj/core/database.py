import sqlite3
from typing import List, Optional, Tuple

from ..models import Config, Features, Song


class MusicDatabase:
    """Database interface for managing music library data.

    Provides methods for storing and retrieving songs, features, and
    managing the SQLite database connection. Supports context manager
    protocol for automatic connection management.
    """

    def __init__(self, config: Config):
        """Initialize the database with configuration.

        :param config: Configuration object containing database path
        """
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "MusicDatabase":
        """Enter context manager, establishing database connection.

        :return: Self reference for use in with statement
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, closing database connection.

        :param exc_type: Exception type if an exception occurred
        :param exc_val: Exception value if an exception occurred
        :param exc_tb: Exception traceback if an exception occurred
        """
        self.close()

    def connect(self) -> None:
        """Establish connection to the SQLite database.

        Creates a new connection if one doesn't exist and sets up
        row factory for dictionary-like access to results.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.config.database_path)
            self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection if open."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the active database connection.

        :return: Active SQLite connection
        :raises RuntimeError: If database is not connected
        """
        if self._conn is None:
            raise RuntimeError(
                "Database not connected. Use context manager or call connect()."
            )
        return self._conn

    def init_db(self) -> None:
        """Initialize database schema.

        Creates the songs and features tables if they don't exist.
        """
        cur = self.connection.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            last_modified REAL,
            duration INTEGER
        )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS features (
            song_id INTEGER PRIMARY KEY,
            feature_vector BLOB,
            bpm REAL,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )""")
        self.connection.commit()

    def add_song(self, song: Song, features: Optional[Features] = None) -> int:
        """Add or update a song and optionally its features.

        :param song: Song object to add or update
        :param features: Optional Features object to associate with the song
        :return: ID of the inserted or updated song
        """
        cur = self.connection.cursor()
        cur.execute(
            """INSERT OR REPLACE INTO songs
                       (file_path, title, artist, album, genre, last_modified, duration)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                song.file_path,
                song.title,
                song.artist,
                song.album,
                song.genre,
                song.last_modified,
                song.duration,
            ),
        )
        song_id = cur.lastrowid

        if features:
            cur.execute(
                """INSERT OR REPLACE INTO features
                           (song_id, feature_vector, bpm)
                           VALUES (?, ?, ?)""",
                (song_id, features.to_bytes(), features.bpm),
            )

        self.connection.commit()
        return song_id

    def get_song(self, song_id: int) -> Optional[Song]:
        """Retrieve a song by its ID.

        :param song_id: ID of the song to retrieve
        :return: Song object if found, None otherwise
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()

        if row:
            return Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
        return None

    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Retrieve a song by its file path.

        :param file_path: File path of the song to retrieve
        :return: Song object if found, None otherwise
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE file_path = ?", (file_path,))
        row = cur.fetchone()

        if row:
            return Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
        return None

    def find_songs_by_title(self, title: str) -> List[Song]:
        """Find songs with titles matching a search pattern.

        :param title: Title search string (supports partial matches)
        :return: List of matching Song objects
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE title LIKE ?", (f"%{title}%",))
        rows = cur.fetchall()

        return [
            Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
            for row in rows
        ]

    def find_song_exact(self, title: str, artist: str, album: str) -> Optional[Song]:
        """Find a song by exact title, artist, and album match.

        :param title: Exact title of the song
        :param artist: Exact artist name
        :param album: Exact album name
        :return: Song object if found, None otherwise
        """
        cur = self.connection.cursor()
        cur.execute(
            "SELECT * FROM songs WHERE title = ? AND artist = ? AND album = ?",
            (title, artist, album),
        )
        row = cur.fetchone()

        if row:
            return Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
        return None

    def get_features(self, song_id: int) -> Optional[Features]:
        """Retrieve features for a specific song.

        :param song_id: ID of the song
        :return: Features object if found, None otherwise
        """
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM features WHERE song_id = ?", (song_id,))
        row = cur.fetchone()

        if row:
            return Features.from_bytes(
                song_id=row["song_id"],
                vector_bytes=row["feature_vector"],
                bpm=row["bpm"],
            )
        return None

    def get_song_with_features(self, song_id: int) -> Optional[Tuple[Song, Features]]:
        """Retrieve a song and its features together.

        :param song_id: ID of the song
        :return: Tuple of (Song, Features) if found, None otherwise
        """
        cur = self.connection.cursor()
        cur.execute(
            """SELECT songs.*, features.feature_vector, features.bpm
                       FROM songs
                       JOIN features ON songs.id = features.song_id
                       WHERE songs.id = ?""",
            (song_id,),
        )
        row = cur.fetchone()

        if row:
            song = Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
            features = Features.from_bytes(
                song_id=row["id"], vector_bytes=row["feature_vector"], bpm=row["bpm"]
            )
            return (song, features)
        return None

    def get_all_songs_with_features(self) -> List[Tuple[Song, Features]]:
        """Retrieve all songs that have features.

        :return: List of (Song, Features) tuples ordered by song ID
        """
        cur = self.connection.cursor()
        cur.execute("""SELECT songs.*, features.feature_vector, features.bpm
                       FROM songs
                       JOIN features ON songs.id = features.song_id
                       ORDER BY songs.id""")
        rows = cur.fetchall()

        results = []
        for row in rows:
            song = Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
            features = Features.from_bytes(
                song_id=row["id"], vector_bytes=row["feature_vector"], bpm=row["bpm"]
            )
            results.append((song, features))

        return results

    def get_all_file_paths_with_mtime(self) -> dict:
        """Get all file paths and their last modified times.

        :return: Dictionary mapping file paths to modification timestamps
        """
        cur = self.connection.cursor()
        cur.execute("SELECT file_path, last_modified FROM songs")
        return {row["file_path"]: row["last_modified"] for row in cur.fetchall()}

    def delete_song(self, file_path: str) -> bool:
        """Delete a song by its file path.

        :param file_path: File path of the song to delete
        :return: True if a song was deleted, False otherwise
        """
        cur = self.connection.cursor()
        cur.execute("DELETE FROM songs WHERE file_path = ?", (file_path,))
        self.connection.commit()
        return cur.rowcount > 0

    def get_songs_by_ids(self, song_ids: List[int]) -> List[Song]:
        """Retrieve multiple songs by their IDs.

        :param song_ids: List of song IDs to retrieve
        :return: List of Song objects for the given IDs
        """
        if not song_ids:
            return []

        cur = self.connection.cursor()
        placeholders = ",".join("?" * len(song_ids))
        cur.execute(f"SELECT * FROM songs WHERE id IN ({placeholders})", song_ids)
        rows = cur.fetchall()

        return [
            Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
            for row in rows
        ]

    def commit(self) -> None:
        """Commit pending database transactions."""
        self.connection.commit()

    def get_songs_without_features(self, file_paths: List[str] = None) -> List[Song]:
        """Get songs that exist in DB but don't have features yet.

        :param file_paths: Optional list of file paths to filter by
        :return: List of Song objects without associated features
        """
        cur = self.connection.cursor()

        if file_paths:
            placeholders = ",".join("?" * len(file_paths))
            query = f"""SELECT songs.* FROM songs 
                       LEFT JOIN features ON songs.id = features.song_id 
                       WHERE features.song_id IS NULL 
                       AND songs.file_path IN ({placeholders})"""
            cur.execute(query, file_paths)
        else:
            query = """SELECT songs.* FROM songs 
                       LEFT JOIN features ON songs.id = features.song_id 
                       WHERE features.song_id IS NULL"""
            cur.execute(query)

        rows = cur.fetchall()
        return [
            Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                album=row["album"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"],
            )
            for row in rows
        ]

    def get_indexing_stats(self) -> dict:
        """Get statistics about indexing progress.

        :return: Dictionary with keys 'total_songs', 'songs_with_features',
                 and 'songs_without_features'
        """
        cur = self.connection.cursor()

        cur.execute("SELECT COUNT(*) FROM songs")
        total_songs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM features")
        songs_with_features = cur.fetchone()[0]

        songs_without_features = total_songs - songs_with_features

        return {
            "total_songs": total_songs,
            "songs_with_features": songs_with_features,
            "songs_without_features": songs_without_features,
        }
