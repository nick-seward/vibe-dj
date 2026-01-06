# Enhanced Audio Feature Extraction Options

This document outlines research findings for adding mood detection, vocal presence, and instrument classification to vibe-dj's audio analysis pipeline.

## Current Feature Vector (50 dimensions)

The existing `AudioAnalyzer.extract_features()` method produces a 50-dimensional vector using librosa:

| Index Range | Dimensions | Feature | Description |
|-------------|------------|---------|-------------|
| 0–12 | 13 | **MFCC** | Mel-Frequency Cepstral Coefficients (timbral texture) |
| 13–44 | 32 | **Chroma** | Pitch class energy distribution (padded from 12) |
| 45 | 1 | **Tempo** | Beats per minute (BPM) |
| 46 | 1 | **Loudness** | RMS energy (volume) |
| 47 | 1 | **Spectral Centroid** | Brightness of sound |
| 48 | 1 | **Danceability** | Derived from onset strength |
| 49 | 1 | **Acousticness** | Derived inverse of loudness + brightness |

### Limitations

The current vector **does not capture**:
- Mood/emotion (relaxed, happy, sad, aggressive)
- Vocal presence or characteristics
- Specific instrument detection
- Semantic audio properties

---

## Recommended Solution: Essentia

**Essentia** is an open-source C++ library with Python bindings from the Music Technology Group (MTG) at Universitat Pompeu Fabra, Barcelona. It provides pre-trained deep learning models specifically designed for music information retrieval.

- **Website**: https://essentia.upf.edu/
- **Models**: https://essentia.upf.edu/models.html
- **License**: AGPLv3

### Installation

```bash
pip install essentia-tensorflow
```

Model weight files (~100-200MB each) must be downloaded separately from the models page.

---

## Available Essentia Models

### Mood and Context Classifiers

| Model | Classes | Use Case |
|-------|---------|----------|
| `mood_relaxed` | relaxed, non_relaxed | Finding calm/chill music |
| `mood_aggressive` | aggressive, non_aggressive | Filtering intense music |
| `mood_happy` | happy, non_happy | Upbeat music detection |
| `mood_sad` | sad, non_sad | Melancholic music detection |
| `mood_party` | party, non_party | High-energy party tracks |
| `mood_acoustic` | acoustic, non_acoustic | Organic vs. electronic sound |
| `mood_electronic` | electronic, non_electronic | Synthesized sound detection |
| `danceability` | danceable, not_danceable | Rhythm-driven music |

### Arousal/Valence Regression

Continuous 2D emotion space (values 1-9):

| Model | Dataset | Description |
|-------|---------|-------------|
| `deam-msd-musicnn` | DEAM | Arousal + Valence regression |
| `emomusic-msd-musicnn` | emoMusic | Alternative emotion dataset |
| `muse-msd-musicnn` | MuSe | Multi-modal emotion dataset |

**Arousal**: Low = calm/relaxed, High = energetic/exciting
**Valence**: Low = sad/negative, High = happy/positive

### Instrumentation

| Model | Classes | Description |
|-------|---------|-------------|
| `mtg_jamendo_instrument` | 40 classes | Multi-label instrument detection |
| `fs_loop_ds` | 5 classes | Loop instrument role (bass, chords, fx, melody, percussion) |

**Instrument classes include**: accordion, acousticbassguitar, acousticguitar, bass, beat, bell, bongo, brass, cello, clarinet, classicalguitar, computer, doublebass, drummachine, drums, electricguitar, electricpiano, flute, guitar, harmonica, harp, horn, keyboard, oboe, orchestra, organ, pad, percussion, piano, pipeorgan, rhodes, sampler, saxophone, strings, synthesizer, trombone, trumpet, viola, violin, voice

### Voice Detection

| Model | Classes | Description |
|-------|---------|-------------|
| `voice_instrumental` | voice, instrumental | Vocal presence detection |
| `gender` | female, male | Singing voice gender classification |

### Engagement/Approachability

| Model | Description |
|-------|-------------|
| `approachability` | Mainstream vs. niche/experimental |
| `engagement` | Active listening vs. background music |

---

## Implementation Options

### Option A: Extend Feature Vector (Unified Search)

Add Essentia-derived features to the existing 50-dimensional vector:

```python
# Extended feature vector structure
current_features = [mfcc(13), chroma(32), tempo, loudness, centroid, danceability, acousticness]  # 50 dims

essentia_features = [
    mood_relaxed,      # 0.0 - 1.0
    mood_aggressive,   # 0.0 - 1.0
    mood_happy,        # 0.0 - 1.0
    mood_sad,          # 0.0 - 1.0
    mood_acoustic,     # 0.0 - 1.0
    voice_presence,    # 0.0 - 1.0
    arousal,           # 1.0 - 9.0 (normalized to 0-1)
    valence,           # 1.0 - 9.0 (normalized to 0-1)
]  # 8 dims

# New total: 58 dimensions
feature_vector = np.concatenate([current_features, essentia_features])
```

**Pros**:
- Single unified FAISS index
- Similarity search considers all properties together
- Simpler query interface

**Cons**:
- Requires re-analyzing entire music library
- Model weights add ~500MB+ to deployment
- All features weighted equally in similarity

### Option B: Hybrid Search with Metadata Filters (Recommended)

Store Essentia predictions as separate metadata columns in SQLite, then use them as pre-filters before FAISS search:

```sql
-- New columns in songs table
ALTER TABLE songs ADD COLUMN mood_relaxed REAL;
ALTER TABLE songs ADD COLUMN mood_acoustic REAL;
ALTER TABLE songs ADD COLUMN voice_presence REAL;
ALTER TABLE songs ADD COLUMN arousal REAL;
ALTER TABLE songs ADD COLUMN valence REAL;
```

Query flow:
1. Filter songs by mood/voice/acoustic thresholds
2. Run FAISS similarity search on filtered subset

```python
# Example: "relaxed vocals with nice instruments"
filtered_songs = db.query("""
    SELECT id FROM songs 
    WHERE mood_relaxed > 0.6 
      AND voice_presence > 0.5 
      AND mood_acoustic > 0.5
      AND arousal < 4.0
""")

# Then search FAISS index for similar songs within filtered set
similar = faiss_index.search(query_vector, k=20, filter=filtered_songs)
```

**Pros**:
- Explicit, interpretable queries
- Can search by specific attributes
- Backward compatible (existing vector unchanged)
- Incremental adoption possible

**Cons**:
- Two-stage search complexity
- May need FAISS index partitioning for efficient filtered search

### Option C: Replace with Deep Embeddings (OpenL3/Discogs-EffNet)

Use a single deep embedding model that captures semantic audio properties:

```python
# OpenL3: 512 or 6144 dimensions
import openl3
embedding, ts = openl3.get_audio_embedding(audio, sr, content_type="music", embedding_size=512)

# Discogs-EffNet: 1280 dimensions
from essentia.standard import TensorflowPredictEffnetDiscogs
embedding_model = TensorflowPredictEffnetDiscogs(graphFilename="discogs-effnet-bs64-1.pb")
embeddings = embedding_model(audio)
```

**Pros**:
- Captures rich semantic properties implicitly
- State-of-the-art similarity matching
- Single model, simpler pipeline

**Cons**:
- Less interpretable (can't query by "relaxed")
- Larger vectors = more storage/memory
- Requires complete re-indexing

---

## Example Code: Essentia Integration

```python
from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs, TensorflowPredict2D
import numpy as np

class EssentiaAnalyzer:
    """Extract mood and vocal features using Essentia pre-trained models."""
    
    def __init__(self, models_path: str):
        self.models_path = models_path
        self._embedding_model = None
        self._classifiers = {}
    
    def _get_embedding_model(self):
        if self._embedding_model is None:
            self._embedding_model = TensorflowPredictEffnetDiscogs(
                graphFilename=f"{self.models_path}/discogs-effnet-bs64-1.pb",
                output="PartitionedCall:1"
            )
        return self._embedding_model
    
    def _get_classifier(self, name: str):
        if name not in self._classifiers:
            self._classifiers[name] = TensorflowPredict2D(
                graphFilename=f"{self.models_path}/{name}-discogs-effnet-1.pb",
                output="model/Softmax"
            )
        return self._classifiers[name]
    
    def extract_features(self, file_path: str) -> dict:
        """Extract mood and vocal features from audio file."""
        # Load audio at 16kHz (required by Essentia models)
        audio = MonoLoader(filename=file_path, sampleRate=16000, resampleQuality=4)()
        
        # Get base embeddings
        embeddings = self._get_embedding_model()(audio)
        
        # Extract classifier predictions
        features = {}
        
        # Mood classifiers (index 0 = positive class probability)
        for mood in ["mood_relaxed", "mood_aggressive", "mood_happy", "mood_sad", "mood_acoustic"]:
            predictions = self._get_classifier(mood)(embeddings)
            features[mood] = float(predictions.mean(axis=0)[0])
        
        # Voice/instrumental (index 1 = voice probability)
        voice_pred = self._get_classifier("voice_instrumental")(embeddings)
        features["voice_presence"] = float(voice_pred.mean(axis=0)[1])
        
        return features


# Usage example
analyzer = EssentiaAnalyzer("/path/to/models")
features = analyzer.extract_features("song.mp3")

print(f"Relaxed: {features['mood_relaxed']:.2f}")
print(f"Vocals: {features['voice_presence']:.2f}")
print(f"Acoustic: {features['mood_acoustic']:.2f}")
```

---

## Query Examples

### "Relaxed vocals with nice instrument background"

```python
# Using metadata filters (Option B)
results = db.query("""
    SELECT * FROM songs 
    WHERE mood_relaxed > 0.6 
      AND voice_presence > 0.5 
      AND mood_acoustic > 0.6
    ORDER BY mood_relaxed DESC
    LIMIT 50
""")
```

### "Upbeat electronic dance music"

```python
results = db.query("""
    SELECT * FROM songs 
    WHERE mood_happy > 0.5 
      AND mood_acoustic < 0.3
      AND danceability > 0.7
    ORDER BY danceability DESC
""")
```

### "Sad acoustic songs without vocals"

```python
results = db.query("""
    SELECT * FROM songs 
    WHERE mood_sad > 0.6 
      AND mood_acoustic > 0.7
      AND voice_presence < 0.3
""")
```

---

## Alternative Libraries

### OpenL3

Deep audio embeddings trained on AudioSet.

```bash
pip install openl3
```

```python
import openl3
import soundfile as sf

audio, sr = sf.read("song.wav")
embedding, timestamps = openl3.get_audio_embedding(
    audio, sr, 
    content_type="music",
    embedding_size=512  # or 6144
)
```

### librosa Vocal Separation (Limited)

Basic harmonic/percussive separation (not recommended for production):

```python
import librosa

y, sr = librosa.load("song.mp3")
S_full, phase = librosa.magphase(librosa.stft(y))
S_filter = librosa.decompose.nn_filter(S_full, aggregate=np.median, metric='cosine')
S_filter = np.minimum(S_full, S_filter)

# Soft masks
mask_v = librosa.util.softmask(S_full - S_filter, S_filter, power=2)
mask_i = librosa.util.softmask(S_filter, S_full - S_filter, power=2)
```

---

## Recommendation

For vibe-dj, **Option B (Hybrid Search with Metadata Filters)** is recommended:

1. **Keep existing librosa features** for acoustic similarity
2. **Add Essentia classifiers** as filterable metadata columns
3. **Query flow**: Filter by mood/voice/acoustic → FAISS search on filtered set

This provides:
- Explicit queryable attributes ("find relaxed songs with vocals")
- Acoustic similarity within filtered results
- Backward compatibility with existing index
- Incremental adoption path

---

## Resources

- Essentia Documentation: https://essentia.upf.edu/
- Essentia Models: https://essentia.upf.edu/models.html
- OpenL3 Documentation: https://openl3.readthedocs.io/
- librosa Documentation: https://librosa.org/doc/
- DEAM Dataset: https://cvml.unige.ch/databases/DEAM/
- MTG-Jamendo Dataset: https://github.com/MTG/mtg-jamendo-dataset
