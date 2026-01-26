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

---

## Beads Issue Tracking

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
```bash
bd create "Follow-up: Add error handling to API endpoint" -p 1 --parent <current-id>
```

2. **Run quality gates** (if code changed)
Tests, linters, builds, type checks — whatever the project requires. Fix failures before proceeding.

3. **Update issue status** - Update in-progress items (e.g., --status=blocked if waiting on something).

4. **Prepare changes for review**
- Stage changes if not already: git add . (or selectively)
- Show what would be committed: git diff --staged or git status
- Stop and request human review — do NOT commit or push yet.
- Tell the human:
  "I have completed work on bead <id>. Here are the changes:"
  Then paste:
  - git diff --staged output (or relevant file diffs)
  - Summary of what was changed
  - Any new/updated beads and notes
  - "Please review the changes. Once you approve, reply with 'Approved' or similar, and I will commit, push, and complete the workflow."

5. **Wait for human approval**
- Do NOT proceed to commit/push until the human explicitly approves (e.g., "Approved", "Looks good", "Proceed").
- If the human requests changes: make fixes, re-run quality gates, and request review again.

6. **Commit, PUSH TO REMOTE, and finish** (only after explicit human approval)
Once approved:
```bash
git commit -m "bd-<id>: [short description of changes]"
git pull --rebase
bd sync
git push
git status     # MUST show "up to date with origin"
```

If push fails, resolve conflicts/errors and retry until it succeeds.

7. **Clean up** - Clear stashes, prune remote branches
```bash
git stash drop    # if any stashes exist
git remote prune origin
```

8. **Verify** - Confirm all changes are committed **and** pushed. No local-only work should remain.
9. **Hand off** - Provide context for the next session
Always leave detailed, persistent context using Beads notes. For every relevant bead (especially in-progress or newly created ones):

```bash
bd note add <id> "Session hand-off [YYYY-MM-DD]: Completed X feature. Key decisions: chose Y approach because Z. Current state: ABC implemented, tests passing locally. Pending: integration tests (see bd-new-id). Pointers: see commit abc1234; review diff for edge cases. No blockers."
```

- Do this before closing any beads.
- Use clear, factual language — treat notes as instructions for the next agent.
- Include: decisions made, rationale, code pointers (commits/files), current state, open questions, and next suggested steps.
- If creating follow-up beads, add initial context notes to them too.

## Note-Writing Best Practices

When adding notes (`bd note add`):
- Be specific and self-contained — the next agent may start from `bd show` without prior chat history.
- Reference commits, files, or external links when helpful.
- Keep notes concise but comprehensive (aim for 3–8 sentences per major update).
- **Never** use interactive commands like `bd edit` (they open an editor agents can't use). Always use `bd update` flags or `bd note add`.

**CRITICAL RULES:**
- NEVER commit or push without explicit human approval.
- Work is NOT complete until human-approved changes are pushed successfully.
- NEVER stop before pushing (after approval) — that strands work locally and breaks continuity.
- NEVER say "ready to push when you are" without first showing diffs and waiting for approval.
- If push fails after approval, diagnose and retry until successful.
- Always prioritize `bd ready` tasks unless explicitly directed otherwise.
- Use Beads exclusively for task tracking — no markdown TODOs or plan files.

## Quick Tips for Agents
- Start every session with: `bd ready` → pick one high-priority unblocked task.
- Claim work before editing: `bd update <id> --status in_progress`.
- Add notes liberally during work — they build durable memory.
- Always request human review before committing/pushing.

Follow these rules strictly — they make multi-session and multi-agent work reliable, amnesia-proof, and human-supervised.
