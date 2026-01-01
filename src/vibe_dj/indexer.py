import os
import time
import musicbrainzngs
from mutagen import File as MutagenFile
from tqdm import tqdm
from multiprocessing import Pool
import multiprocessing
from .db import get_connection, init_db
from .analyzer import fetch_acousticbrainz_features, librosa_fallback_features
from .utils import get_duration
from .config import FAISS_INDEX_PATH
import faiss
import numpy as np
from loguru import logger


musicbrainzngs.set_useragent("MusicDJ", "0.1", "nick@homeslice.ca")

def extract_metadata(file_path: str):
    audio = MutagenFile(file_path, easy=True)
    title = (audio.get("title", [os.path.basename(file_path)]) or [os.path.basename(file_path)])[0]
    artist = (audio.get("artist", ["Unknown"]) or ["Unknown"])[0]
    genre = (audio.get("genre", ["Unknown"]) or ["Unknown"])[0]

    mbid = None
    if audio:
        mbid = audio.get("musicbrainz_recordingid") or audio.get("musicbrainz_trackid")
        if mbid:
            mbid = mbid[0]

    if not mbid:
        try:
            results = musicbrainzngs.search_recordings(recording=title, artist=artist, limit=1)
            if results.get("recording-list"):
                mbid = results["recording-list"][0]["id"]
            time.sleep(1)
        except Exception:
            pass

    return title, artist, genre, mbid

def process_file(file_path: str):
    """Process a single file - runs in worker process, so NO database access allowed."""
    filename = os.path.basename(file_path)
    title, artist, genre, mbid = extract_metadata(file_path)
    duration = get_duration(file_path)

    # Always use librosa in worker processes to avoid database connection issues
    # AcousticBrainz caching would require shared state which doesn't work with multiprocessing
    method = "librosa"
    features, bpm = librosa_fallback_features(file_path)

    mtime = os.path.getmtime(file_path)
    return (file_path, title, artist, genre, mbid, mtime, duration, features, bpm, method, filename)

def index_library(library_path: str):
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    supported = ('.mp3', '.flac', '.wav', '.ogg')
    files = [os.path.join(root, f) for root, _, fs in os.walk(library_path) for f in fs if f.lower().endswith(supported)]

    existing = {}
    cur.execute("SELECT file_path, last_modified FROM songs")
    for row in cur.fetchall():
        existing[row["file_path"]] = row["last_modified"]

    to_process = [f for f in files if f not in existing or os.path.getmtime(f) > existing[f]]

    if to_process:
        print(f"\nIndexing {len(to_process)} new/modified songs...")
        
        # Limit pool size to prevent memory explosion
        # Use at most 4 workers to control concurrent librosa loads
        num_workers = 4
        
        batch_size = 10  # Process and commit in batches to release memory
        processed_count = 0
        failed_count = 0
        acousticbrainz_count = 0
        librosa_count = 0
        
        with Pool(processes=num_workers) as pool:
            # Use imap for streaming results instead of loading all into memory
            pbar = tqdm(total=len(to_process), desc="Processing", unit="song")
            
            for result in pool.imap(process_file, to_process, chunksize=1):
                file_path, title, artist, genre, mbid, mtime, duration, features, bpm, method, filename = result
                
                # Update progress bar with current file info
                pbar.set_postfix_str(f"{artist} - {title} [{method}]")
                pbar.update(1)
                
                if features is not None:
                    cur.execute("""INSERT OR REPLACE INTO songs
                                   (file_path, title, artist, genre, mbid, last_modified, duration)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (file_path, title, artist, genre, mbid, mtime, duration))
                    song_id = cur.lastrowid
                    cur.execute("""INSERT OR REPLACE INTO features
                                   (song_id, feature_vector, bpm)
                                   VALUES (?, ?, ?)""",
                                (song_id, features.tobytes(), bpm))
                    
                    processed_count += 1
                    if method == "acousticbrainz":
                        acousticbrainz_count += 1
                    else:
                        librosa_count += 1
                    
                    # Commit in batches to release memory and ensure data persistence
                    if processed_count % batch_size == 0:
                        conn.commit()
                else:
                    failed_count += 1
                    logger.warning(f"Failed to extract features: {filename}")
            
            pbar.close()

        # Final commit for any remaining records
        conn.commit()
        
        # Clean up deleted files
        scanned_set = set(files)
        cur.execute("SELECT file_path FROM songs")
        for row in cur.fetchall():
            if row["file_path"] not in scanned_set:
                cur.execute("DELETE FROM songs WHERE file_path = ?", (row["file_path"],))

        conn.commit()

        # Print summary statistics
        print(f"\n{'='*60}")
        print(f"Indexing Summary:")
        print(f"  Successfully processed: {processed_count}/{len(to_process)} songs")
        print(f"  Failed: {failed_count}")
        print(f"  AcousticBrainz: {acousticbrainz_count}")
        print(f"  Librosa (local): {librosa_count}")
        print(f"{'='*60}\n")

        # Rebuild FAISS index
        print("Building similarity index...")
        cur.execute("SELECT feature_vector FROM features")
        vectors = [np.frombuffer(row["feature_vector"], dtype=np.float32) for row in cur.fetchall()]
        if vectors:
            dim = len(vectors[0])
            index = faiss.IndexFlatL2(dim)
            index.add(np.array(vectors))
            faiss.write_index(index, FAISS_INDEX_PATH)
            print(f"Index built with {len(vectors)} songs.")
    else:
        print("No new or modified songs to process.")

    conn.close()
    print("\nIndexing complete.")
