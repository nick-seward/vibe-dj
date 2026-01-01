import sqlite3
import json
import faiss
import numpy as np
from .config import DATABASE_PATH, FAISS_INDEX_PATH, PLAYLIST_OUTPUT

def generate_playlist(seeds: list[str], length: int = 20, output_path: str = PLAYLIST_OUTPUT):
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    # Find seed songs
    seed_vectors = []
    seed_ids = []
    for seed in seeds:
        cur.execute("""SELECT songs.id, feature_vector FROM songs
                       JOIN features ON songs.id = features.song_id
                       WHERE title LIKE ?""", (f"%{seed}%",))
        row = cur.fetchone()
        if row:
            seed_ids.append(row["id"])
            seed_vectors.append(np.frombuffer(row["feature_vector"], dtype=np.float32))

    if not seed_vectors:
        raise ValueError("No seed songs found.")

    avg_vector = np.mean(seed_vectors, axis=0).reshape(1, -1)

    index = faiss.read_index(FAISS_INDEX_PATH)
    D, I = index.search(avg_vector, length + len(seeds) + 50)  # Extra for variety

    playlist = []
    used_ids = set(seed_ids)
    for idx in I[0]:
        if len(playlist) >= length:
            break
        cur.execute("""SELECT songs.id, title, artist, duration, file_path, bpm
                       FROM songs JOIN features ON songs.id = features.song_id
                       WHERE songs.id = ?""", (idx,))
        row = cur.fetchone()
        if row and row["id"] not in used_ids:
            used_ids.add(row["id"])
            playlist.append({
                "id": row["id"],
                "title": row["title"],
                "artist": row["artist"],
                "duration": row["duration"] or -1,
                "file_path": row["file_path"],
                "bpm": row["bpm"]
            })

    # Simple flow: sort by BPM ascending
    playlist.sort(key=lambda x: x["bpm"])

    # Write extended M3U
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for song in playlist:
            f.write(f"#EXTINF:{song['duration']},{song['artist']} - {song['title']}\n")
            f.write(f"{song['file_path']}\n")

    conn.close()
    return playlist
