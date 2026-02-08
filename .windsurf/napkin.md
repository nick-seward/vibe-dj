# Napkin

## Corrections
| Date | Source | What Went Wrong | What To Do Instead |
|------|--------|----------------|-------------------|
| 2026-02-07 | user | Pushed code then ran `bd close` + `bd comments add`, leaving `.beads/issues.jsonl` uncommitted | After `bd close`/`bd comments add`/`bd sync`, always run `git status` to check for uncommitted beads files, then commit and push them |

## User Preferences
- Uses `bd comments add <id> "text"` not `bd note add` for beads
- Follow AGENTS.md workflow strictly: claim bead, do work, run tests, request review before commit

## Patterns That Work
- (accumulate here as you learn them)

## Patterns That Don't Work
- (approaches that failed and why)

## Domain Notes
- Project uses uv for Python deps, npm for UI deps
- Tests: pytest (Python), Vitest (UI)
- Linting: Ruff (Python), ESLint (TypeScript)
- `make test` runs all Python tests, `cd ui && npm run test:run` for UI tests
