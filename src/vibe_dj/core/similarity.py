from typing import List, Tuple

import faiss
import numpy as np
from loguru import logger

from ..models import Config


class SimilarityIndex:
    def __init__(self, config: Config):
        self.config = config
        self._index: faiss.IndexIDMap = None
        self._dimension: int = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def size(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal

    def build_index(self, vectors: np.ndarray, song_ids: np.ndarray) -> None:
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
        if self._index is None:
            raise RuntimeError("No index to save. Build or load an index first.")

        if path is None:
            path = self.config.faiss_index_path

        faiss.write_index(self._index, path)
        logger.info(f"Saved similarity index to {path}")

    def load(self, path: str = None) -> None:
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
        if self._index is None:
            raise RuntimeError("Index not initialized.")

        song_ids_int64 = np.array(song_ids, dtype=np.int64)
        self._index.remove_ids(song_ids_int64)
