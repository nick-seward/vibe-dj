import random
import numpy as np
from typing import List, Optional
from loguru import logger
from ..models import Config, Song, Features, Playlist
from ..core.database import MusicDatabase
from ..core.similarity import SimilarityIndex


class PlaylistGenerator:
    def __init__(self, config: Config, database: MusicDatabase, similarity_index: SimilarityIndex):
        self.config = config
        self.database = database
        self.similarity_index = similarity_index

    def find_seed_songs(self, seed_titles: List[str]) -> List[Song]:
        seed_songs = []
        
        for seed_title in seed_titles:
            matches = self.database.find_songs_by_title(seed_title)
            
            if matches:
                seed_songs.append(matches[0])
                logger.info(f"Found seed song: {matches[0]}")
            else:
                logger.warning(f"No match found for seed: {seed_title}")
        
        return seed_songs

    def get_seed_vectors(self, seed_songs: List[Song]) -> List[np.ndarray]:
        vectors = []
        
        for song in seed_songs:
            features = self.database.get_features(song.id)
            if features:
                vectors.append(features.feature_vector)
            else:
                logger.warning(f"No features found for seed song: {song}")
        
        return vectors

    def compute_average_vector(self, vectors: List[np.ndarray]) -> np.ndarray:
        if not vectors:
            raise ValueError("No vectors to average")
        
        return np.mean(vectors, axis=0)

    def find_similar_songs(self, query_vector: np.ndarray, count: int, 
                          exclude_ids: set) -> List[Song]:
        extra_buffer = 50
        distances, indices = self.similarity_index.search(
            query_vector, 
            k=count + len(exclude_ids) + extra_buffer
        )
        
        similar_songs = []
        for song_id in indices:
            if len(similar_songs) >= count:
                break
            
            if int(song_id) not in exclude_ids:
                song_with_features = self.database.get_song_with_features(int(song_id))
                if song_with_features:
                    song, _ = song_with_features
                    similar_songs.append(song)
        
        return similar_songs

    def sort_by_bpm(self, songs: List[Song], bpm_jitter_percent: float = 5.0) -> List[Song]:
        songs_with_bpm = []
        
        for song in songs:
            features = self.database.get_features(song.id)
            if features:
                jitter = random.uniform(
                    -bpm_jitter_percent / 100, 
                    bpm_jitter_percent / 100
                )
                adjusted_bpm = features.bpm * (1 + jitter)
                songs_with_bpm.append((song, adjusted_bpm))
        
        songs_with_bpm.sort(key=lambda x: x[1])
        
        return [song for song, _ in songs_with_bpm]

    def generate(self, seed_titles: List[str], length: int = 20, 
                bpm_jitter_percent: float = 5.0) -> Optional[Playlist]:
        if not seed_titles:
            raise ValueError("At least one seed title is required")
        
        seed_songs = self.find_seed_songs(seed_titles)
        
        if not seed_songs:
            raise ValueError("No seed songs found in database")
        
        seed_vectors = self.get_seed_vectors(seed_songs)
        
        if not seed_vectors:
            raise ValueError("No features found for seed songs")
        
        avg_vector = self.compute_average_vector(seed_vectors)
        
        exclude_ids = {song.id for song in seed_songs}
        similar_songs = self.find_similar_songs(avg_vector, length, exclude_ids)
        
        if not similar_songs:
            logger.warning("No similar songs found")
            return None
        
        sorted_songs = self.sort_by_bpm(similar_songs, bpm_jitter_percent)
        
        playlist = Playlist(
            songs=sorted_songs,
            seed_songs=seed_songs
        )
        
        logger.info(f"Generated playlist with {len(playlist)} songs")
        return playlist
