import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration settings for the vibe-dj application.

    Contains paths, audio analysis parameters, processing settings,
    and optional Navidrome integration credentials.
    """

    music_library: str = ""
    database_path: str = "music.db"
    faiss_index_path: str = "faiss_index.bin"
    playlist_output: str = "playlist.m3u"

    sample_rate: int = 22050
    max_duration: int = 180
    n_mfcc: int = 13

    parallel_workers: int = field(default_factory=lambda: os.cpu_count() or 4)
    batch_size: int = 10
    processing_timeout: int = 30

    query_noise_scale: float = 0.1
    candidate_multiplier: int = 4

    navidrome_url: Optional[str] = None
    navidrome_username: Optional[str] = None
    navidrome_password: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.music_library and not os.path.exists(self.music_library):
            raise ValueError(f"Music library path does not exist: {self.music_library}")
        if self.music_library and not os.path.isdir(self.music_library):
            raise ValueError(
                f"Music library path is not a directory: {self.music_library}"
            )

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from a JSON file.

        :param path: Path to the JSON configuration file
        :return: Config instance with loaded settings
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def save(self, path: str) -> None:
        """Save configuration to a JSON file.

        :param path: Path where the configuration should be saved
        """
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create configuration from a dictionary.

        Only includes keys that match Config dataclass fields.

        :param data: Dictionary containing configuration values
        :return: Config instance with values from dictionary
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
