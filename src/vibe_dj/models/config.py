import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
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

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
