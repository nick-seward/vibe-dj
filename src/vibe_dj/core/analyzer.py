import numpy as np
import librosa
import math
from typing import Optional, Tuple
from mutagen import File as MutagenFile
import musicbrainzngs
import time
from loguru import logger
from ..models import Song, Features, Config


musicbrainzngs.set_useragent("MusicDJ", "0.1", "nick@homeslice.ca")


class AudioAnalyzer:
    def __init__(self, config: Config):
        self.config = config

    def extract_features(self, file_path: str) -> Optional[Features]:
        try:
            y, sr = librosa.load(
                file_path,
                sr=self.config.sample_rate,
                mono=True,
                duration=self.config.max_duration
            )
            
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.config.n_mfcc).mean(axis=1)
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
            
            feature_vector = np.concatenate([
                mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]
            ]).astype(np.float32)

            return Features(
                song_id=0,
                feature_vector=feature_vector,
                bpm=float(tempo)
            )
        except Exception as e:
            logger.error(f"Failed to extract features from {file_path}: {e}")
            return None


    def extract_metadata(self, file_path: str) -> Tuple[str, str, str, Optional[str]]:
        try:
            audio = MutagenFile(file_path, easy=True)
            title = (audio.get("title", [None]) or [None])[0]
            if not title:
                import os
                title = os.path.basename(file_path)
            
            artist = (audio.get("artist", ["Unknown"]) or ["Unknown"])[0]
            genre = (audio.get("genre", ["Unknown"]) or ["Unknown"])[0]

            mbid = None
            if audio:
                mbid = audio.get("musicbrainz_recordingid") or audio.get("musicbrainz_trackid")
                if mbid:
                    mbid = mbid[0]

            if not mbid:
                try:
                    results = musicbrainzngs.search_recordings(
                        recording=title,
                        artist=artist,
                        limit=1
                    )
                    if results.get("recording-list"):
                        mbid = results["recording-list"][0]["id"]
                    time.sleep(1)
                except Exception:
                    pass

            return title, artist, genre, mbid
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            import os
            return os.path.basename(file_path), "Unknown", "Unknown", None

    def get_duration(self, file_path: str) -> Optional[int]:
        try:
            audio = MutagenFile(file_path)
            if audio and audio.info:
                return int(math.ceil(audio.info.length))
        except Exception as e:
            logger.error(f"Failed to get duration from {file_path}: {e}")
        return None

    def analyze_file(self, file_path: str, last_modified: float) -> Optional[Tuple[Song, Features]]:
        title, artist, genre, mbid = self.extract_metadata(file_path)
        duration = self.get_duration(file_path)
        features = self.extract_features(file_path)
        
        if features is None:
            return None
        
        song = Song(
            id=0,
            file_path=file_path,
            title=title,
            artist=artist,
            genre=genre,
            mbid=mbid,
            last_modified=last_modified,
            duration=duration
        )
        
        return (song, features)
