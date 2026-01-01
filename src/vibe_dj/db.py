import sqlite3
from .config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        title TEXT,
        artist TEXT,
        genre TEXT,
        mbid TEXT,
        last_modified REAL,
        duration INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS features (
        song_id INTEGER PRIMARY KEY,
        feature_vector BLOB,
        bpm REAL,
        FOREIGN KEY(song_id) REFERENCES songs(id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS acousticbrainz_cache (
        mbid TEXT PRIMARY KEY,
        low_level TEXT,
        high_level TEXT,
        fetched_at REAL
    )''')
    conn.commit()
    conn.close()