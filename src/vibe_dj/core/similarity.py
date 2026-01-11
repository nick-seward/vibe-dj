from typing import List, Tuple

import faiss
import numpy as np
from loguru import logger

from vibe_dj.models import Config


class SimilarityIndex:
    """Manages FAISS-based similarity index for nearest neighbor search.

    Provides methods to build, save, load, and query a FAISS index that
    maps song feature vectors to song IDs for efficient similarity search.
    """

    def __init__(self, config: Config):
        """Initialize the similarity index with configuration.

        :param config: Configuration object containing index path
        """
        self.config = config
        self._index: faiss.IndexIDMap = None
        self._dimension: int = None

    @property
    def dimension(self) -> int:
        """Get the dimensionality of the feature vectors.

        :return: Feature vector dimension
        """
        return self._dimension

    @property
    def size(self) -> int:
        """Get the number of vectors in the index.

        :return: Number of indexed vectors, or 0 if index not built
        """
        if self._index is None:
            return 0
        return self._index.ntotal

    def build_index(self, vectors: np.ndarray, song_ids: np.ndarray) -> None:
        """Build a new similarity index from scratch.

        Creates a new FAISS IndexIDMap with L2 distance metric and adds
        all provided vectors with their corresponding song IDs.

        :param vectors: 2D array of feature vectors (n_songs x dimension)
        :param song_ids: 1D array of song IDs corresponding to vectors
        :raises ValueError: If vectors array is empty or lengths don't match
        """
        if len(vectors) == 0:
            raise ValueError("Cannot build index with empty vectors")

        if len(vectors) != len(song_ids):
            raise ValueError("Number of vectors must match number of song IDs")

        self._dimension = vectors.shape[1]

        base_index = faiss.IndexFlatL2(self._dimension)
        self._index = faiss.IndexIDMap(base_index)

        vectors_float32 = vectors.astype(np.float32)
        song_ids_int64 = song_ids.astype(np.int64)

        self._index.add_with_ids(vectors_float32, song_ids_int64)

        logger.info(
            f"Built similarity index with {len(vectors)} songs, dimension {self._dimension}"
        )

    def search(
        self, query_vector: np.ndarray, k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors to a query vector.

        :param query_vector: Feature vector to search for
        :param k: Number of nearest neighbors to return
        :return: Tuple of (distances, song_ids) arrays
        :raises RuntimeError: If index is not built or loaded
        :raises ValueError: If query vector dimension doesn't match index
        """
        if self._index is None:
            raise RuntimeError("Index not built. Call build_index() or load() first.")

        if query_vector.shape[-1] != self._dimension:
            raise ValueError(
                f"Query vector dimension {query_vector.shape[-1]} does not match index dimension {self._dimension}"
            )

        query_vector = query_vector.reshape(1, -1).astype(np.float32)

        distances, indices = self._index.search(query_vector, k)

        return distances[0], indices[0]

    def save(self, path: str = None) -> None:
        """Save the index to disk.

        :param path: Optional path to save to, defaults to config path
        :raises RuntimeError: If no index exists to save
        """
        if self._index is None:
            raise RuntimeError("No index to save. Build or load an index first.")

        if path is None:
            path = self.config.faiss_index_path

        faiss.write_index(self._index, path)
        logger.info(f"Saved similarity index to {path}")

    def load(self, path: str = None) -> None:
        """Load an index from disk.

        :param path: Optional path to load from, defaults to config path
        :raises Exception: If loading fails
        """
        if path is None:
            path = self.config.faiss_index_path

        try:
            self._index = faiss.read_index(path)

            if hasattr(self._index, "index"):
                self._dimension = self._index.index.d
            else:
                self._dimension = self._index.d

            logger.info(f"Loaded similarity index from {path} with {self.size} songs")
        except Exception as e:
            logger.error(f"Failed to load index from {path}: {e}")
            raise

    def add_vectors(self, vectors: np.ndarray, song_ids: np.ndarray) -> None:
        """Add new vectors to an existing index.

        :param vectors: 2D array of feature vectors to add
        :param song_ids: 1D array of song IDs corresponding to vectors
        :raises RuntimeError: If index is not initialized
        :raises ValueError: If lengths don't match or dimensions don't match
        """
        if self._index is None:
            raise RuntimeError("Index not initialized. Call build_index() first.")

        if len(vectors) != len(song_ids):
            raise ValueError("Number of vectors must match number of song IDs")

        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} does not match index dimension {self._dimension}"
            )

        vectors_float32 = vectors.astype(np.float32)
        song_ids_int64 = song_ids.astype(np.int64)

        self._index.add_with_ids(vectors_float32, song_ids_int64)

    def remove_vectors(self, song_ids: List[int]) -> None:
        """Remove vectors from the index by song IDs.

        :param song_ids: List of song IDs to remove
        :raises RuntimeError: If index is not initialized
        """
        if self._index is None:
            raise RuntimeError("Index not initialized.")

        song_ids_int64 = np.array(song_ids, dtype=np.int64)
        self._index.remove_ids(song_ids_int64)
