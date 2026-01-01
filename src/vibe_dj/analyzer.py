import numpy as np
import librosa
import requests
import json
import time
from loguru import logger
import os

from .db import get_connection
from .config import USE_ACOUSTICBRAINZ


def fetch_acousticbrainz_features(mbid: str | None):
    if not USE_ACOUSTICBRAINZ or not mbid:
        logger.debug("AcousticBrainz disabled or no MBID - skipping API attempt")
        return None, None

    logger.debug(f"Processing mbid={mbid}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT low_level, high_level FROM acousticbrainz_cache WHERE mbid = ?", (mbid,))
    row = cur.fetchone()

    if row and row[0]:
        logger.debug("Cache hit")
        ll_data = json.loads(row[0])
        hl_data = json.loads(row[1]) if row[1] else {}
    else:
        logger.debug("Cache miss - fetching from API")
        ll_data, hl_data = _fetch_from_api(mbid, cur)
        if ll_data is not None:
            cur.execute("""INSERT OR REPLACE INTO acousticbrainz_cache
                           (mbid, low_level, high_level, fetched_at)
                           VALUES (?, ?, ?, ?)""",
                        (mbid, json.dumps(ll_data), json.dumps(hl_data) if hl_data else None, time.time()))
            conn.commit()
            logger.debug("Cached new AcousticBrainz data")
        else:
            logger.debug("API fetch failed - will use local analysis")
    conn.close()

    if ll_data is None:
        return None, None

    return _parse_features(ll_data, hl_data)

def _fetch_from_api(mbid: str, cur):
    ll_url = f"https://acousticbrainz.org/api/v1/{mbid}/low-level?n=0"
    hl_url = f"https://acousticbrainz.org/api/v1/{mbid}/high-level?n=0"

    ll_data = None
    hl_data = {}

    try:
        logger.debug("Requesting low-level data...")
        ll_resp = requests.get(ll_url, timeout=3)
        if ll_resp.status_code == 404:
            logger.debug("Low-level 404 - no data for this MBID")
            return None, None
        ll_resp.raise_for_status()
        ll_data = ll_resp.json()
        logger.debug("Low-level fetched successfully")
    except requests.exceptions.ConnectionError:
        logger.debug("Connection error on low-level request")
        return None, None
    except requests.exceptions.Timeout:
        logger.debug("Timeout on low-level request")
        return None, None
    except requests.exceptions.RequestException as e:
        logger.debug(f"Low-level request error: {e}")
        return None, None

    try:
        logger.debug("Requesting high-level data...")
        hl_resp = requests.get(hl_url, timeout=3)
        if hl_resp.status_code == 200:
            hl_data = hl_resp.json()
            logger.debug("High-level fetched successfully")
        else:
            logger.debug(f"High-level returned {hl_resp.status_code} - no high-level data available")
    except Exception as e:
        logger.debug(f"High-level request error: {e}")

    time.sleep(0.5)
    return ll_data, hl_data

def _parse_features(ll_data: dict, hl_data: dict):
    try:
        mfcc = np.array(ll_data['lowlevel']['mfcc']['mean'][:13])
        hpcp = np.mean(ll_data['tonal']['hpcp']['all'], axis=0)[:32]
        bpm = ll_data['rhythm']['bpm']
        energy = ll_data['lowlevel']['average_loudness']
        centroid = ll_data['lowlevel']['spectral_centroid']['mean']

        # Safe defaults for high-level (many recordings lack these models)
        hl = hl_data.get('highlevel', {})
        dance_all = hl.get('danceability', {}).get('all', {})
        acoustic_all = hl.get('mood_acoustic', {}).get('all', {})

        dance = dance_all.get('danceable', 0.5)
        acoustic = acoustic_all.get('acoustic', 0.5)

        if not dance_all:
            logger.debug("No danceability high-level data - using default 0.5")
        if not acoustic_all:
            logger.debug("No mood_acoustic high-level data - using default 0.5")

        features = np.concatenate([mfcc, hpcp, [bpm, energy, centroid, dance, acoustic]]).astype(np.float32)
        logger.debug("AcousticBrainz features parsed successfully")
        return features, float(bpm)
    except KeyError as e:
        logger.debug(f"Missing expected AcousticBrainz field: {e}")
        return None, None
    except Exception as e:
        logger.warning(f"Error parsing AcousticBrainz features: {e}")
        return None, None

def librosa_fallback_features(file_path: str):
    logger.info(f"Using local audio analysis for {os.path.basename(file_path)}")
    try:
        # Load with duration limit to prevent excessive memory usage on very long files
        y, sr = librosa.load(file_path, sr=22050, mono=True, duration=180)
        
        # Extract all features while audio is in memory
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)[:32]
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        loudness = librosa.feature.rms(y=y).mean()
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        onset_strength = librosa.onset.onset_strength(y=y, sr=sr).mean()
        danceability = onset_strength / 10.0
        acousticness = 1.0 - (loudness + centroid / sr)

        # Explicitly delete audio array to free memory immediately
        del y
        
        features = np.concatenate([
            mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]
        ]).astype(np.float32)

        logger.info(f"Extracted features from {os.path.basename(file_path)} (BPM: {tempo:.1f})")
        return features, float(tempo)
    except Exception as e:
        logger.error(f"Audio analysis failed for {os.path.basename(file_path)}: {e}")
        return None, None