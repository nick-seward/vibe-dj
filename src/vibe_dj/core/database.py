import sqlite3
from typing import List, Optional, Tuple
from ..models import Song, Features, Config


class MusicDatabase:
    def __init__(self, config: Config):
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "MusicDatabase":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self) -> None:
        if self._conn is None:
            self._conn = sqlite3.connect(self.config.database_path)
            self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Use context manager or call connect().")
        return self._conn

    def init_db(self) -> None:
        cur = self.connection.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            title TEXT,
            artist TEXT,
            genre TEXT,
            last_modified REAL,
            duration INTEGER
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS features (
            song_id INTEGER PRIMARY KEY,
            feature_vector BLOB,
            bpm REAL,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )''')
        self.connection.commit()

    def add_song(self, song: Song, features: Optional[Features] = None) -> int:
        cur = self.connection.cursor()
        cur.execute("""INSERT OR REPLACE INTO songs
                       (file_path, title, artist, genre, last_modified, duration)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (song.file_path, song.title, song.artist, song.genre,
                     song.last_modified, song.duration))
        song_id = cur.lastrowid
        
        if features:
            cur.execute("""INSERT OR REPLACE INTO features
                           (song_id, feature_vector, bpm)
                           VALUES (?, ?, ?)""",
                        (song_id, features.to_bytes(), features.bpm))
        
        self.connection.commit()
        return song_id

    def get_song(self, song_id: int) -> Optional[Song]:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()
        
        if row:
            return Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"]
            )
        return None

    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE file_path = ?", (file_path,))
        row = cur.fetchone()
        
        if row:
            return Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"]
            )
        return None

    def find_songs_by_title(self, title: str) -> List[Song]:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM songs WHERE title LIKE ?", (f"%{title}%",))
        rows = cur.fetchall()
        
        return [Song(
            id=row["id"],
            file_path=row["file_path"],
            title=row["title"],
            artist=row["artist"],
            genre=row["genre"],
            last_modified=row["last_modified"],
            duration=row["duration"]
        ) for row in rows]

    def get_features(self, song_id: int) -> Optional[Features]:
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM features WHERE song_id = ?", (song_id,))
        row = cur.fetchone()
        
        if row:
            return Features.from_bytes(
                song_id=row["song_id"],
                vector_bytes=row["feature_vector"],
                bpm=row["bpm"]
            )
        return None

    def get_song_with_features(self, song_id: int) -> Optional[Tuple[Song, Features]]:
        cur = self.connection.cursor()
        cur.execute("""SELECT songs.*, features.feature_vector, features.bpm
                       FROM songs
                       JOIN features ON songs.id = features.song_id
                       WHERE songs.id = ?""", (song_id,))
        row = cur.fetchone()
        
        if row:
            song = Song(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                artist=row["artist"],
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"]
            )
            features = Features.from_bytes(
                song_id=row["id"],
                vector_bytes=row["feature_vector"],
                bpm=row["bpm"]
            )
            return (song, features)
        return None

    def get_all_songs_with_features(self) -> List[Tuple[Song, Features]]:
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
                genre=row["genre"],
                last_modified=row["last_modified"],
                duration=row["duration"]
            )
            features = Features.from_bytes(
                song_id=row["id"],
                vector_bytes=row["feature_vector"],
                bpm=row["bpm"]
            )
            results.append((song, features))
        
        return results

    def get_all_file_paths_with_mtime(self) -> dict:
        cur = self.connection.cursor()
        cur.execute("SELECT file_path, last_modified FROM songs")
        return {row["file_path"]: row["last_modified"] for row in cur.fetchall()}

    def delete_song(self, file_path: str) -> bool:
        cur = self.connection.cursor()
        cur.execute("DELETE FROM songs WHERE file_path = ?", (file_path,))
        self.connection.commit()
        return cur.rowcount > 0

    def get_songs_by_ids(self, song_ids: List[int]) -> List[Song]:
        if not song_ids:
            return []
        
        cur = self.connection.cursor()
        placeholders = ','.join('?' * len(song_ids))
        cur.execute(f"SELECT * FROM songs WHERE id IN ({placeholders})", song_ids)
        rows = cur.fetchall()
        
        return [Song(
            id=row["id"],
            file_path=row["file_path"],
            title=row["title"],
            artist=row["artist"],
            genre=row["genre"],
            last_modified=row["last_modified"],
            duration=row["duration"]
        ) for row in rows]

    def commit(self) -> None:
        self.connection.commit()
