import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from tqdm import tqdm

from ..models import Config, Features, Song
from .analyzer import AudioAnalyzer
from .database import MusicDatabase
from .similarity import SimilarityIndex


def _worker_thread_file(args: Tuple[str, AudioAnalyzer]) -> Tuple[str, Optional[Features], Optional[float]]:
    file_path, analyzer = args
    features = analyzer.extract_features(file_path)
    
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

    def extract_metadata_phase(self, files: List[str]) -> int:
        """Extract and immediately persist metadata. Returns count of processed files."""
        logger.info("=== Phase 1: Extracting metadata ===")
        
        processed = 0
        for file_path in tqdm(files, desc="Metadata extraction", unit="song"):
            title, artist, album, genre = self.analyzer.extract_metadata(file_path)
            duration = self.analyzer.get_duration(file_path)
            mtime = os.path.getmtime(file_path)
            
            song = Song(
                id=0,
                file_path=file_path,
                title=title,
                artist=artist,
                album=album,
                genre=genre,
                last_modified=mtime,
                duration=duration
            )
            
            self.database.add_song(song, features=None)
            processed += 1
            
            if processed % self.config.batch_size == 0:
                self.database.commit()
        
        self.database.commit()
        logger.info(f"Phase 1 complete: {processed} songs with metadata saved")
        return processed

    def extract_features_phase(self) -> int:
        """Extract features for songs missing them. Returns count processed."""
        songs_needing_features = self.database.get_songs_without_features()
        
        if not songs_needing_features:
            logger.info("All songs already have features")
            return 0
        
        logger.info(f"=== Phase 2: Processing with librosa ({len(songs_needing_features)} songs) ===")
        
        file_paths = [song.file_path for song in songs_needing_features]
        processed = 0
        timeout_seconds = self.config.processing_timeout
        
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            args_list = [(f, self.analyzer) for f in file_paths]
            future_to_file = {executor.submit(_worker_thread_file, args): args[0] for args in args_list}
            
            try:
                with tqdm(total=len(file_paths), desc="Librosa analysis", unit="song") as pbar:
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            result_file_path, features, bpm = future.result(timeout=timeout_seconds)
                            
                            if features is not None:
                                song = self.database.get_song_by_path(result_file_path)
                                if song:
                                    self.database.add_song(song, features)
                                    processed += 1
                                    
                                    if processed % self.config.batch_size == 0:
                                        self.database.commit()
                            else:
                                logger.warning(f"Failed to process: {result_file_path}")
                        except TimeoutError:
                            logger.warning(f"Timeout ({timeout_seconds}s) processing: {file_path}")
                        except Exception as e:
                            logger.error(f"Error processing {file_path}: {e}")
                        finally:
                            pbar.update(1)
                
                self.database.commit()
                logger.info(f"Phase 2 complete: {processed} songs with features saved")
            except KeyboardInterrupt:
                logger.info("Interrupted by user, shutting down executor...")
                self.database.commit()
                executor.shutdown(wait=False, cancel_futures=True)
                raise
        
        return processed


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
        """Rebuild the entire similarity index from scratch."""
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

    def update_similarity_index_incremental(self, new_song_count: int) -> None:
        """Update similarity index incrementally or rebuild if necessary."""
        import os
        
        stats = self.database.get_indexing_stats()
        total_with_features = stats['songs_with_features']
        
        if total_with_features == 0:
            logger.info("No songs with features, skipping index update")
            return
        
        index_exists = os.path.exists(self.config.faiss_index_path)
        
        if not index_exists:
            logger.info("No existing index found, building from scratch")
            self.rebuild_similarity_index()
            return
        
        try:
            self.similarity_index.load()
            current_index_size = self.similarity_index.size
            
            change_percentage = (new_song_count / max(current_index_size, 1)) * 100
            
            if change_percentage > 10:
                logger.info(f"Large update ({change_percentage:.1f}% change), rebuilding index")
                self.rebuild_similarity_index()
            else:
                logger.info(f"Small update ({new_song_count} songs), updating incrementally")
                
                songs_with_features = self.database.get_all_songs_with_features()
                all_song_ids = {song.id for song, _ in songs_with_features}
                
                new_songs = [(song, features) for song, features in songs_with_features 
                            if song.id > current_index_size or song.id not in all_song_ids]
                
                if new_songs:
                    vectors = np.array([features.feature_vector for _, features in new_songs])
                    song_ids = np.array([song.id for song, _ in new_songs], dtype=np.int64)
                    
                    self.similarity_index.add_vectors(vectors, song_ids)
                    self.similarity_index.save()
                    logger.info(f"Added {len(new_songs)} songs to index")
                else:
                    logger.info("No new songs to add to index")
        except Exception as e:
            logger.warning(f"Failed to update index incrementally: {e}. Rebuilding from scratch.")
            self.rebuild_similarity_index()

    def index_library(self, library_path: str) -> None:
        """Index the music library with resumable incremental processing."""
        self.database.init_db()
        
        stats = self.database.get_indexing_stats()
        if stats['total_songs'] > 0:
            logger.info("=" * 60)
            logger.info("Existing Progress:")
            logger.info(f"  Total songs in database: {stats['total_songs']}")
            logger.info(f"  Songs with features: {stats['songs_with_features']}")
            logger.info(f"  Songs without features: {stats['songs_without_features']}")
            logger.info("=" * 60)
        
        all_files = self.scan_files(library_path)
        files_to_process = self.get_files_to_process(all_files)
        
        metadata_count = 0
        features_count = 0
        
        if files_to_process:
            logger.info(f"Indexing {len(files_to_process)} new/modified songs...")
            metadata_count = self.extract_metadata_phase(files_to_process)
        else:
            logger.info("No new or modified songs found.")
        
        features_count = self.extract_features_phase()
        
        deleted_count = self.clean_deleted_files(all_files)
        
        final_stats = self.database.get_indexing_stats()
        logger.info("=" * 60)
        logger.info("Indexing Summary:")
        logger.info(f"  Metadata extracted: {metadata_count} songs")
        logger.info(f"  Features extracted: {features_count} songs")
        if deleted_count > 0:
            logger.info(f"  Deleted files removed: {deleted_count}")
        logger.info(f"  Total in database: {final_stats['total_songs']} songs")
        logger.info(f"  Complete with features: {final_stats['songs_with_features']} songs")
        logger.info("=" * 60)
        
        if features_count > 0 or metadata_count > 0:
            self.update_similarity_index_incremental(features_count)
        
        logger.info("Indexing complete.")
