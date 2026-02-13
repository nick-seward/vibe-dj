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

This project uses **bd** (beads) for issue tracking.

Key invariants:

- `.beads/` is authoritative state and **must always be committed** with code changes.
- Do not edit `.beads/*.jsonl` directly; only via `bd`.
- **bd is non-invasive**: it NEVER executes git commands. You must manually commit `.beads/` changes.

### Basics

Check ready work:

```bash
bd ready --json
```

Create issues:

```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bv-123 --json
```

Update:

```bash
bd update bv-42 --status in_progress --json
bd update bv-42 --priority 1 --json
```

Complete:

```bash
bd close bv-42 --reason "Completed" --json
```

Types:

- `bug`, `feature`, `task`, `epic`, `chore`

Priorities:

- `0` critical (security, data loss, broken builds)
- `1` high
- `2` medium (default)
- `3` low
- `4` backlog

Agent workflow:

1. `bd ready` to find unblocked work.
2. Claim: `bd update <id> --status in_progress`.
3. Implement + test.
4. If you discover new work, create a new bead with `discovered-from:<parent-id>`.
5. Close when done.
6. Sync and commit:
   ```bash
   bd sync --flush-only    # Export to JSONL (no git ops)
   git add .beads/         # Stage beads changes
   git commit -m "..."     # Commit with code changes
   ```

Never:

- Use markdown TODO lists.
- Use other trackers.
- Duplicate tracking.

---

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

---

## Using bv as an AI Sidecar

bv is a graph-aware triage engine for Beads projects (.beads/beads.jsonl). Instead of parsing JSONL or hallucinating graph traversal, use robot flags for deterministic, dependency-aware outputs with precomputed metrics (PageRank, betweenness, critical path, cycles, HITS, eigenvector, k-core).

**Scope boundary:** bv handles *what to work on* (triage, priority, planning).

**⚠️ CRITICAL: Use ONLY `--robot-*` flags. Bare `bv` launches an interactive TUI that blocks your session.**

### The Workflow: Start With Triage

**`bv --robot-triage` is your single entry point.** It returns everything you need in one call:
- `quick_ref`: at-a-glance counts + top 3 picks
- `recommendations`: ranked actionable items with scores, reasons, unblock info
- `quick_wins`: low-effort high-impact items
- `blockers_to_clear`: items that unblock the most downstream work
- `project_health`: status/type/priority distributions, graph metrics
- `commands`: copy-paste shell commands for next steps

```bash
bv --robot-triage        # THE MEGA-COMMAND: start here
bv --robot-next          # Minimal: just the single top pick + claim command
```

### Other Commands

**Planning:**
| Command | Returns |
|---------|---------|
| `--robot-plan` | Parallel execution tracks with `unblocks` lists |
| `--robot-priority` | Priority misalignment detection with confidence |

**Graph Analysis:**
| Command | Returns |
|---------|---------|
| `--robot-insights` | Full metrics: PageRank, betweenness, HITS, eigenvector, critical path, cycles, k-core, articulation points, slack |
| `--robot-label-health` | Per-label health: `health_level` (healthy\|warning\|critical), `velocity_score`, `staleness`, `blocked_count` |
| `--robot-label-flow` | Cross-label dependency: `flow_matrix`, `dependencies`, `bottleneck_labels` |
| `--robot-label-attention [--attention-limit=N]` | Attention-ranked labels by: (pagerank × staleness × block_impact) / velocity |

**History & Change Tracking:**
| Command | Returns |
|---------|---------|
| `--robot-history` | Bead-to-commit correlations: `stats`, `histories` (per-bead events/commits/milestones), `commit_index` |
| `--robot-diff --diff-since <ref>` | Changes since ref: new/closed/modified issues, cycles introduced/resolved |

**Other Commands:**
| Command | Returns |
|---------|---------|
| `--robot-burndown <sprint>` | Sprint burndown, scope changes, at-risk items |
| `--robot-forecast <id\|all>` | ETA predictions with dependency-aware scheduling |
| `--robot-alerts` | Stale issues, blocking cascades, priority mismatches |
| `--robot-suggest` | Hygiene: duplicates, missing deps, label suggestions, cycle breaks |
| `--robot-graph [--graph-format=json\|dot\|mermaid]` | Dependency graph export |
| `--export-graph <file.html>` | Self-contained interactive HTML visualization |

### Scoping & Filtering

```bash
bv --robot-plan --label backend              # Scope to label's subgraph
bv --robot-insights --as-of HEAD~30          # Historical point-in-time
bv --recipe actionable --robot-plan          # Pre-filter: ready to work (no blockers)
bv --recipe high-impact --robot-triage       # Pre-filter: top PageRank scores
bv --robot-triage --robot-triage-by-track    # Group by parallel work streams
bv --robot-triage --robot-triage-by-label    # Group by domain
```

### Understanding Robot Output

**All robot JSON includes:**
- `data_hash` — Fingerprint of source beads.jsonl (verify consistency across calls)
- `status` — Per-metric state: `computed|approx|timeout|skipped` + elapsed ms
- `as_of` / `as_of_commit` — Present when using `--as-of`; contains ref and resolved SHA

**Two-phase analysis:**
- **Phase 1 (instant):** degree, topo sort, density — always available immediately
- **Phase 2 (async, 500ms timeout):** PageRank, betweenness, HITS, eigenvector, cycles — check `status` flags

**For large graphs (>500 nodes):** Some metrics may be approximated or skipped. Always check `status`.

### jq Quick Reference

```bash
bv --robot-triage | jq '.quick_ref'                        # At-a-glance summary
bv --robot-triage | jq '.recommendations[0]'               # Top recommendation
bv --robot-plan | jq '.plan.summary.highest_impact'        # Best unblock target
bv --robot-insights | jq '.status'                         # Check metric readiness
bv --robot-insights | jq '.Cycles'                         # Circular deps (must fix!)
bv --robot-label-health | jq '.results.labels[] | select(.health_level == "critical")'
```

**Performance:** Phase 1 instant, Phase 2 async (500ms timeout). Prefer `--robot-plan` over `--robot-insights` when speed matters. Results cached by data hash. Use `bv --profile-startup` for diagnostics.

Use bv instead of parsing beads.jsonl—it computes PageRank, critical paths, cycles, and parallel tracks deterministically.