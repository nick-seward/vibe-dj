import random
from typing import List, Optional

import numpy as np
from loguru import logger

from ..core.database import MusicDatabase
from ..core.similarity import SimilarityIndex
from ..models import Config, Features, Playlist, Song


class PlaylistGenerator:
    def __init__(self, config: Config, database: MusicDatabase, similarity_index: SimilarityIndex):
        self.config = config
        self.database = database
        self.similarity_index = similarity_index

    def find_seed_songs(self, seed_data: List[dict]) -> List[Song]:
        seed_songs = []
        
        for seed in seed_data:
            if not isinstance(seed, dict):
                logger.error(f"Invalid seed format: {seed}. Expected dict with 'title', 'artist', 'album'")
                continue
            
            title = seed.get('title')
            artist = seed.get('artist')
            album = seed.get('album')
            
            if not title or not artist or not album:
                logger.error(f"Missing required fields in seed: {seed}. Need 'title', 'artist', and 'album'")
                continue
            
            match = self.database.find_song_exact(title, artist, album)
            
            if match:
                seed_songs.append(match)
                logger.info(f"Found seed song: {match}")
            else:
                logger.warning(f"No exact match found for seed: {title} by {artist} from {album}")
        
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

    def perturb_query_vector(self, query_vector: np.ndarray, noise_scale: float = None) -> np.ndarray:
        if noise_scale is None:
            noise_scale = self.config.query_noise_scale
        
        if noise_scale <= 0:
            return query_vector
        
        vector_std = np.std(query_vector)
        noise = np.random.normal(0, vector_std * noise_scale, query_vector.shape)
        
        return query_vector + noise

    def find_similar_songs(self, query_vector: np.ndarray, count: int, 
                          exclude_ids: set, candidate_multiplier: int = None) -> List[Song]:
        if candidate_multiplier is None:
            candidate_multiplier = self.config.candidate_multiplier
        
        extra_buffer = 50
        candidate_count = count * candidate_multiplier
        
        distances, indices = self.similarity_index.search(
            query_vector, 
            k=candidate_count + len(exclude_ids) + extra_buffer
        )
        
        candidate_songs = []
        for song_id in indices:
            if int(song_id) not in exclude_ids:
                song_with_features = self.database.get_song_with_features(int(song_id))
                if song_with_features:
                    song, _ = song_with_features
                    candidate_songs.append(song)
                    
                    if len(candidate_songs) >= candidate_count:
                        break
        
        if len(candidate_songs) <= count:
            return candidate_songs
        
        selected_indices = random.sample(range(len(candidate_songs)), count)
        return [candidate_songs[i] for i in selected_indices]

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

    def generate(self, seed_data: List[dict], length: int = 20, 
                bpm_jitter_percent: float = 5.0, query_noise_scale: float = None,
                candidate_multiplier: int = None) -> Optional[Playlist]:
        if not seed_data:
            raise ValueError("At least one seed is required")
        
        seed_songs = self.find_seed_songs(seed_data)
        
        if not seed_songs:
            raise ValueError("No seed songs found in database")
        
        seed_vectors = self.get_seed_vectors(seed_songs)
        
        if not seed_vectors:
            raise ValueError("No features found for seed songs")
        
        avg_vector = self.compute_average_vector(seed_vectors)
        
        perturbed_vector = self.perturb_query_vector(avg_vector, query_noise_scale)
        
        exclude_ids = {song.id for song in seed_songs}
        similar_songs = self.find_similar_songs(
            perturbed_vector, length, exclude_ids, candidate_multiplier
        )
        
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
