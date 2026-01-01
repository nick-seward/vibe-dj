import numpy as np
import librosa
from loguru import logger


def extract_features_librosa(file_path: str):
    try:
        # Load with duration limit to prevent excessive memory usage on very long files
        y, sr = librosa.load(file_path, sr=22050, mono=True, duration=180)
        
        # Extract all features while audio is in memory
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        chroma = np.pad(chroma, (0, 32 - len(chroma)), mode='constant')
        
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if np.isscalar(tempo) else float(tempo[0])
        
        loudness = float(librosa.feature.rms(y=y).mean())
        centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
        onset_strength = float(librosa.onset.onset_strength(y=y, sr=sr).mean())
        danceability = float(onset_strength / 10.0)
        acousticness = float(1.0 - (loudness + centroid / sr))

        # Explicitly delete audio array to free memory immediately
        del y
        
        features = np.concatenate([
            mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]
        ]).astype(np.float32)

        return features, float(tempo)
    except Exception as e:
        return None, None