import os
import time
import musicbrainzngs
from mutagen import File as MutagenFile
from tqdm import tqdm
from multiprocessing import Pool
from .db import get_connection, init_db
from .analyzer import extract_features_librosa
from .utils import get_duration
from .config import FAISS_INDEX_PATH
import faiss
import numpy as np
from loguru import logger


musicbrainzngs.set_useragent("MusicDJ", "0.1", "nick@homeslice.ca")

def _worker_process_file(file_path: str):
    """Worker function for multiprocessing - must be at module level."""
    import librosa
    import numpy as np
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Processing timeout")
    
    try:
        # Set 30 second timeout for processing each file
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        y, sr = librosa.load(file_path, sr=22050, mono=True, duration=180)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        chroma = np.pad(chroma, (0, 32 - len(chroma)), mode='constant')
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if np.isscalar(tempo) else float(tempo[0])
        loudness = float(librosa.feature.rms(y=y).mean())
        centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
        onset_strength = float(librosa.onset.onset_strength(y=y, sr=sr).mean())
        danceability = float(onset_strength / 10.0)
        acousticness = float(1.0 - (loudness + centroid / sr))
        del y
        features = np.concatenate([
            mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]
        ]).astype(np.float32)
        
        signal.alarm(0)  # Cancel alarm
        return file_path, features, float(tempo)
    except TimeoutError:
        signal.alarm(0)
        return file_path, None, None
    except Exception:
        signal.alarm(0)
        return file_path, None, None

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
        logger.info(f"Indexing {len(to_process)} new/modified songs...")
        
        # PHASE 1: Extract metadata
        logger.info("=== Phase 1: Extracting metadata ===")
        file_metadata = []
        for file_path in tqdm(to_process, desc="Metadata extraction", unit="song"):
            title, artist, genre, mbid = extract_metadata(file_path)
            duration = get_duration(file_path)
            mtime = os.path.getmtime(file_path)
            file_metadata.append({
                'file_path': file_path,
                'title': title,
                'artist': artist,
                'genre': genre,
                'mbid': mbid,
                'mtime': mtime,
                'duration': duration
            })
        
        # PHASE 2: Parallel librosa processing
        logger.info(f"=== Phase 2: Processing with librosa ({len(to_process)} songs) ===")
        librosa_results = {}
        pool = Pool(processes=4)
        try:
            results_iter = pool.imap_unordered(_worker_process_file, to_process, chunksize=1)
            for file_path, features, bpm in tqdm(
                results_iter,
                total=len(to_process),
                desc="Librosa analysis",
                unit="song"):
                if features is not None:
                    librosa_results[file_path] = (features, bpm)
                else:
                    logger.warning(f"Failed to process: {file_path}")
            logger.info("  All librosa processing complete, closing pool...")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, terminating workers...")
            pool.terminate()
            pool.join()
            raise
        except Exception as e:
            logger.error(f"Error during librosa processing: {e}")
            pool.terminate()
            pool.join()
            raise
        else:
            pool.close()
            pool.join()
            logger.info("  Pool closed successfully")
        
        # Write all results to database
        logger.info("=== Writing results to database ===")
        processed_count = 0
        failed_count = 0
        batch_size = 10
        
        for meta in tqdm(file_metadata, desc="Database writes", unit="song"):
            file_path = meta['file_path']
            
            if file_path in librosa_results:
                features, bpm = librosa_results[file_path]
                
                cur.execute("""INSERT OR REPLACE INTO songs
                               (file_path, title, artist, genre, mbid, last_modified, duration)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (file_path, meta['title'], meta['artist'], meta['genre'], 
                             meta['mbid'], meta['mtime'], meta['duration']))
                song_id = cur.lastrowid
                cur.execute("""INSERT OR REPLACE INTO features
                               (song_id, feature_vector, bpm)
                               VALUES (?, ?, ?)""",
                            (song_id, features.tobytes(), bpm))
                
                processed_count += 1
                
                if processed_count % batch_size == 0:
                    conn.commit()
            else:
                failed_count += 1
                logger.warning(f"Failed to extract features: {meta['title']}")
        
        conn.commit()
        
        # Clean up deleted files
        scanned_set = set(files)
        cur.execute("SELECT file_path FROM songs")
        for row in cur.fetchall():
            if row["file_path"] not in scanned_set:
                cur.execute("DELETE FROM songs WHERE file_path = ?", (row["file_path"],))

        conn.commit()

        # Print summary statistics
        logger.info("="*60)
        logger.info("Indexing Summary:")
        logger.info(f"  Successfully processed: {processed_count}/{len(to_process)} songs")
        logger.info(f"  Failed: {failed_count}")
        logger.info("="*60)

        # Rebuild FAISS index
        logger.info("Building similarity index...")
        cur.execute("SELECT feature_vector FROM features")
        vectors = [np.frombuffer(row["feature_vector"], dtype=np.float32) for row in cur.fetchall()]
        if vectors:
            dim = len(vectors[0])
            index = faiss.IndexFlatL2(dim)
            index.add(np.array(vectors))
            faiss.write_index(index, FAISS_INDEX_PATH)
            logger.info(f"Index built with {len(vectors)} songs.")
    else:
        logger.info("No new or modified songs to process.")

    conn.close()
    logger.info("Indexing complete.")
