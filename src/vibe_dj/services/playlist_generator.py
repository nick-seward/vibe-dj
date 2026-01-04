import random
from typing import List, Optional

import numpy as np
from loguru import logger

from ..core.database import MusicDatabase
from ..core.similarity import SimilarityIndex
from ..models import Config, Features, Playlist, Song


class PlaylistGenerator:
    """Generates playlists based on seed songs using similarity search.

    Uses audio feature similarity and BPM sorting to create cohesive
    playlists from seed songs.
    """

    def __init__(
        self, config: Config, database: MusicDatabase, similarity_index: SimilarityIndex
    ):
        """Initialize the playlist generator.

        :param config: Configuration object
        :param database: Database interface for song and feature access
        :param similarity_index: Similarity index for nearest neighbor search
        """
        self.config = config
        self.database = database
        self.similarity_index = similarity_index

    def find_seed_songs(self, seed_data: List[dict]) -> List[Song]:
        """Find seed songs in the database from seed data.

        :param seed_data: List of dictionaries with 'title', 'artist', 'album' keys
        :return: List of matching Song objects found in database
        """
        seed_songs = []

        for seed in seed_data:
            if not isinstance(seed, dict):
                logger.error(
                    f"Invalid seed format: {seed}. Expected dict with 'title', 'artist', 'album'"
                )
                continue

            title = seed.get("title")
            artist = seed.get("artist")
            album = seed.get("album")

            if not title or not artist or not album:
                logger.error(
                    f"Missing required fields in seed: {seed}. Need 'title', 'artist', and 'album'"
                )
                continue

            match = self.database.find_song_exact(title, artist, album)

            if match:
                seed_songs.append(match)
                logger.info(f"Found seed song: {match}")
            else:
                logger.warning(
                    f"No exact match found for seed: {title} by {artist} from {album}"
                )

        return seed_songs

    def get_seed_vectors(self, seed_songs: List[Song]) -> List[np.ndarray]:
        """Extract feature vectors for seed songs.

        :param seed_songs: List of seed Song objects
        :return: List of feature vectors for the seed songs
        """
        vectors = []

        for song in seed_songs:
            features = self.database.get_features(song.id)
            if features:
                vectors.append(features.feature_vector)
            else:
                logger.warning(f"No features found for seed song: {song}")

        return vectors

    def compute_average_vector(self, vectors: List[np.ndarray]) -> np.ndarray:
        """Compute the average of multiple feature vectors.

        :param vectors: List of feature vectors to average
        :return: Average feature vector
        :raises ValueError: If vectors list is empty
        """
        if not vectors:
            raise ValueError("No vectors to average")

        return np.mean(vectors, axis=0)

    def perturb_query_vector(
        self, query_vector: np.ndarray, noise_scale: float = None
    ) -> np.ndarray:
        """Add random noise to query vector for diversity.

        :param query_vector: Original query vector
        :param noise_scale: Scale of noise relative to vector std (defaults to config value)
        :return: Perturbed query vector
        """
        if noise_scale is None:
            noise_scale = self.config.query_noise_scale

        if noise_scale <= 0:
            return query_vector

        vector_std = np.std(query_vector)
        noise = np.random.normal(0, vector_std * noise_scale, query_vector.shape)

        return query_vector + noise

    def find_similar_songs(
        self,
        query_vector: np.ndarray,
        count: int,
        exclude_ids: set,
        candidate_multiplier: int = None,
    ) -> List[Song]:
        """Find similar songs using nearest neighbor search with random sampling.

        Searches for more candidates than needed and randomly samples from them
        to add diversity to the playlist.

        :param query_vector: Query feature vector
        :param count: Number of songs to return
        :param exclude_ids: Set of song IDs to exclude from results
        :param candidate_multiplier: Multiplier for candidate pool size (defaults to config value)
        :return: List of similar Song objects
        """
        if candidate_multiplier is None:
            candidate_multiplier = self.config.candidate_multiplier

        extra_buffer = 50
        candidate_count = count * candidate_multiplier

        distances, indices = self.similarity_index.search(
            query_vector, k=candidate_count + len(exclude_ids) + extra_buffer
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

    def sort_by_bpm(
        self, songs: List[Song], bpm_jitter_percent: float = 5.0
    ) -> List[Song]:
        """Sort songs by BPM with random jitter for smooth transitions.

        Adds small random variations to BPM values before sorting to avoid
        rigid ordering while maintaining general tempo progression.

        :param songs: List of songs to sort
        :param bpm_jitter_percent: Percentage of BPM jitter to apply
        :return: List of songs sorted by adjusted BPM
        """
        songs_with_bpm = []

        for song in songs:
            features = self.database.get_features(song.id)
            if features:
                jitter = random.uniform(
                    -bpm_jitter_percent / 100, bpm_jitter_percent / 100
                )
                adjusted_bpm = features.bpm * (1 + jitter)
                songs_with_bpm.append((song, adjusted_bpm))

        songs_with_bpm.sort(key=lambda x: x[1])

        return [song for song, _ in songs_with_bpm]

    def generate(
        self,
        seed_data: List[dict],
        length: int = 20,
        bpm_jitter_percent: float = 5.0,
        query_noise_scale: float = None,
        candidate_multiplier: int = None,
    ) -> Optional[Playlist]:
        """Generate a playlist based on seed songs.

        Main entry point for playlist generation. Finds seed songs, computes
        average feature vector, searches for similar songs, and sorts by BPM.

        :param seed_data: List of seed song dictionaries with 'title', 'artist', 'album'
        :param length: Number of songs to generate
        :param bpm_jitter_percent: BPM jitter percentage for sorting
        :param query_noise_scale: Noise scale for query perturbation (defaults to config value)
        :param candidate_multiplier: Candidate pool multiplier (defaults to config value)
        :return: Generated Playlist object, or None if no similar songs found
        :raises ValueError: If no seed data provided or no seed songs found
        """
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

        playlist = Playlist(songs=sorted_songs, seed_songs=seed_songs)

        logger.info(f"Generated playlist with {len(playlist)} songs")
        return playlist
