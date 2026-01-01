import os
from typing import List, Dict, Tuple
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np
from loguru import logger
from ..models import Config, Song, Features
from .database import MusicDatabase
from .analyzer import AudioAnalyzer
from .similarity import SimilarityIndex


def _worker_process_file(args: Tuple[str, Config]) -> Tuple[str, Features, float]:
    file_path, config = args
    analyzer = AudioAnalyzer(config)
    features = analyzer.extract_features_with_timeout(file_path)
    
    if features:
        return (file_path, features, features.bpm)
    return (file_path, None, None)


class LibraryIndexer:
    SUPPORTED_EXTENSIONS = ('.mp3', '.flac', '.wav', '.ogg')
    
    def __init__(self, config: Config, database: MusicDatabase, 
                 analyzer: AudioAnalyzer, similarity_index: SimilarityIndex):
        self.config = config
        self.database = database
        self.analyzer = analyzer
        self.similarity_index = similarity_index

    def scan_files(self, library_path: str) -> List[str]:
        files = []
        for root, _, fs in os.walk(library_path):
            for f in fs:
                if f.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    files.append(os.path.join(root, f))
        
        logger.info(f"Found {len(files)} audio files in {library_path}")
        return files

    def get_files_to_process(self, files: List[str]) -> List[str]:
        existing = self.database.get_all_file_paths_with_mtime()
        
        to_process = []
        for f in files:
            if f not in existing or os.path.getmtime(f) > existing[f]:
                to_process.append(f)
        
        logger.info(f"{len(to_process)} new/modified files to process")
        return to_process

    def extract_metadata_phase(self, files: List[str]) -> Dict[str, dict]:
        logger.info("=== Phase 1: Extracting metadata ===")
        
        file_metadata = {}
        for file_path in tqdm(files, desc="Metadata extraction", unit="song"):
            title, artist, genre, mbid = self.analyzer.extract_metadata(file_path)
            duration = self.analyzer.get_duration(file_path)
            mtime = os.path.getmtime(file_path)
            
            file_metadata[file_path] = {
                'title': title,
                'artist': artist,
                'genre': genre,
                'mbid': mbid,
                'mtime': mtime,
                'duration': duration
            }
        
        return file_metadata

    def extract_features_phase(self, files: List[str]) -> Dict[str, Tuple[Features, float]]:
        logger.info(f"=== Phase 2: Processing with librosa ({len(files)} songs) ===")
        
        features_results = {}
        pool = Pool(processes=self.config.parallel_workers)
        
        try:
            args_list = [(f, self.config) for f in files]
            results_iter = pool.imap_unordered(_worker_process_file, args_list, chunksize=1)
            
            for file_path, features, bpm in tqdm(
                results_iter,
                total=len(files),
                desc="Librosa analysis",
                unit="song"
            ):
                if features is not None:
                    features_results[file_path] = (features, bpm)
                else:
                    logger.warning(f"Failed to process: {file_path}")
            
            logger.info("All librosa processing complete, closing pool...")
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
            logger.info("Pool closed successfully")
        
        return features_results

    def write_to_database(self, file_metadata: Dict[str, dict], 
                         features_results: Dict[str, Tuple[Features, float]]) -> Tuple[int, int]:
        logger.info("=== Writing results to database ===")
        
        processed_count = 0
        failed_count = 0
        
        for file_path, meta in tqdm(file_metadata.items(), desc="Database writes", unit="song"):
            if file_path in features_results:
                features, bpm = features_results[file_path]
                
                song = Song(
                    id=0,
                    file_path=file_path,
                    title=meta['title'],
                    artist=meta['artist'],
                    genre=meta['genre'],
                    mbid=meta['mbid'],
                    last_modified=meta['mtime'],
                    duration=meta['duration']
                )
                
                self.database.add_song(song, features)
                processed_count += 1
                
                if processed_count % self.config.batch_size == 0:
                    self.database.commit()
            else:
                failed_count += 1
                logger.warning(f"Failed to extract features: {meta['title']}")
        
        self.database.commit()
        return processed_count, failed_count

    def clean_deleted_files(self, scanned_files: List[str]) -> int:
        scanned_set = set(scanned_files)
        existing_paths = self.database.get_all_file_paths_with_mtime()
        
        deleted_count = 0
        for file_path in existing_paths:
            if file_path not in scanned_set:
                self.database.delete_song(file_path)
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Removed {deleted_count} deleted files from database")
            self.database.commit()
        
        return deleted_count

    def rebuild_similarity_index(self) -> None:
        logger.info("Building similarity index...")
        
        songs_with_features = self.database.get_all_songs_with_features()
        
        if not songs_with_features:
            logger.warning("No songs with features found, skipping index build")
            return
        
        vectors = np.array([features.feature_vector for _, features in songs_with_features])
        song_ids = np.array([song.id for song, _ in songs_with_features], dtype=np.int64)
        
        self.similarity_index.build_index(vectors, song_ids)
        self.similarity_index.save()
        
        logger.info(f"Index built with {len(vectors)} songs")

    def index_library(self, library_path: str) -> None:
        self.database.init_db()
        
        all_files = self.scan_files(library_path)
        files_to_process = self.get_files_to_process(all_files)
        
        if files_to_process:
            logger.info(f"Indexing {len(files_to_process)} new/modified songs...")
            
            file_metadata = self.extract_metadata_phase(files_to_process)
            features_results = self.extract_features_phase(files_to_process)
            processed_count, failed_count = self.write_to_database(file_metadata, features_results)
            
            self.clean_deleted_files(all_files)
            
            logger.info("=" * 60)
            logger.info("Indexing Summary:")
            logger.info(f"  Successfully processed: {processed_count}/{len(files_to_process)} songs")
            logger.info(f"  Failed: {failed_count}")
            logger.info("=" * 60)
            
            self.rebuild_similarity_index()
        else:
            logger.info("No new or modified songs to process.")
        
        logger.info("Indexing complete.")
