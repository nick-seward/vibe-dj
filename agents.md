# Agents Guide for Vibe-DJ

## Project Overview

Vibe-DJ is a music library indexer and intelligent playlist generator that uses audio feature analysis and similarity search. The application has a **Python backend** (FastAPI) and a **React frontend** (TypeScript/Vite).

### Key Technologies

- **Backend**: Python 3.14, FastAPI, SQLAlchemy, FAISS, librosa
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, Framer Motion
- **Testing**: pytest (Python), Vitest (UI)
- **Linting**: Ruff (Python), ESLint (TypeScript)

### Architecture

```
src/vibe_dj/          # Python backend
├── api/              # FastAPI routes (config, index, playlist, songs)
├── core/             # Business logic (database, analyzer, indexer, similarity)
├── models/           # Pydantic models and SQLAlchemy ORM
├── services/         # External integrations (Navidrome, playlist export)
└── app.py            # FastAPI application entry point

ui/src/               # React frontend
├── components/       # React components (ConfigScreen, MusicTab, PlaylistView, etc.)
├── context/          # React context providers
└── App.tsx           # Main application component
```

### Core Functionality

1. **Indexing**: Scans music libraries and extracts audio features using librosa
2. **Similarity Search**: Uses FAISS for efficient vector similarity search
3. **Playlist Generation**: Creates playlists based on seed songs with BPM-based sorting
4. **Navidrome Sync**: Optionally syncs generated playlists to Navidrome/Subsonic servers

---

## Dev Environment Tips

### Python Dependencies with uv

[uv](https://docs.astral.sh/uv/) is used for Python dependency management. Dependencies are defined in `pyproject.toml`.

```bash
# Create virtual environment
uv venv

# Install all dependencies including test group
uv sync --all-groups

# Add a new dependency
uv add <package-name>

# Add a dev/test dependency
uv add --group test <package-name>

# Run a command in the virtual environment
uv run <command>
```

### JavaScript/TypeScript Dependencies with npm

The UI uses npm for dependency management. The `package.json` is located in the `ui/` directory.

```bash
# Install dependencies
cd ui && npm install

# Add a new dependency
cd ui && npm install <package-name>

# Add a dev dependency
cd ui && npm install --save-dev <package-name>
```

### Installing Everything with Make

The `Makefile` provides convenient commands for setup and common tasks:

```bash
# Clean build artifacts, caches, and node_modules
make clean

# Install all Python and JavaScript dependencies
make install
```

The `make install` command runs:
1. `uv sync --all-groups` - Installs Python dependencies
2. `cd ui && npm install` - Installs JavaScript dependencies

### Running the Application

```bash
# Start both API and UI (builds UI first)
make run

# Start API server only (http://localhost:8000)
make api-server

# Start UI dev server only (http://localhost:5173)
make ui-server
```

---

## Testing Instructions

### Python Unit Tests

Python tests use pytest and are located in the `tests/` directory.

```bash
# Run all Python tests
make test

# Or directly with pytest
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/core/test_database.py -v

# Run tests with coverage report
make codecov
```

**Test structure:**
- `tests/unit/` - Unit tests organized by module (api, core, models, services)
- `tests/integration/` - Integration tests
- `tests/test_api.py` - API endpoint tests

### UI Unit Tests

UI tests use Vitest with React Testing Library and are located alongside components with `.test.tsx` suffix.

```bash
# Run UI tests in watch mode
cd ui && npm test

# Run UI tests once (CI mode)
cd ui && npm run test:run

# Run UI tests with coverage
cd ui && npm run test:coverage
```

**Test files:**
- `ui/src/components/ConfigScreen.test.tsx`
- `ui/src/components/SearchForm.test.tsx`
- `ui/src/components/SearchResults.test.tsx`

### Important

**All tests must always pass.** If tests are failing, they should be fixed before proceeding with other work. Run both Python and UI tests to ensure full coverage:

```bash
make test && cd ui && npm run test:run
```

---

## Code Style Guidelines

### Python

Python code uses **Ruff** for linting and formatting. Configuration is in `pyproject.toml`.

```bash
# Format code
make format

# Lint and fix import sorting
make lint
```

**Style rules:**
- Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Use docstrings with `:param:` and `:return:` format for public functions
- Imports should be sorted (Ruff handles this with `--select I`)
- Maximum line length: default Ruff settings (88 characters)

**Example:**
```python
def generate_playlist(
    seed_song_ids: list[int],
    playlist_length: int = 20,
) -> list[Song]:
    """Generate a playlist based on seed songs.

    :param seed_song_ids: List of song IDs to use as seeds
    :param playlist_length: Number of songs in the playlist
    :return: List of Song objects
    """
    ...
```

### TypeScript/JavaScript

TypeScript code uses **ESLint** with TypeScript and React plugins. Configuration is in `ui/eslint.config.js`.

```bash
# Lint UI code
cd ui && npm run lint
```

**Style rules:**
- Use TypeScript for all new code (`.tsx` for components, `.ts` for utilities)
- Use functional components with hooks (no class components)
- Use named exports for components
- Use `interface` for object types, `type` for unions/aliases
- Follow React hooks rules (enforced by eslint-plugin-react-hooks)

**Example:**
```typescript
interface SongCardProps {
  song: Song;
  onSelect?: (song: Song) => void;
}

export function SongCard({ song, onSelect }: SongCardProps) {
  return (
    <div onClick={() => onSelect?.(song)}>
      {song.title}
    </div>
  );
}
```
