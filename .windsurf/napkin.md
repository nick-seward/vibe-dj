# Napkin

## Corrections
| Date | Source | What Went Wrong | What To Do Instead |
|------|--------|----------------|-------------------|
| 2026-02-07 | user | Pushed code then ran `bd close` + `bd comments add`, leaving `.beads/issues.jsonl` uncommitted | After `bd close`/`bd comments add`/`bd sync`, always run `git status` to check for uncommitted beads files, then commit and push them |
| 2026-02-07 | user | After creating beads, immediately claimed one and started building Docker image without being asked | Only create the beads when asked to create them. Do NOT auto-claim or start work unless the user explicitly says to |
| 2026-02-07 | self | Switching from editable to non-editable install broke UI serving — `__file__` resolves to site-packages, not /app/src/ | When changing install mode, check all `__file__`-relative paths. Added VIBE_DJ_UI_PATH env var as fix. |
| 2026-02-12 | user | Read `.beads/issues.jsonl` directly instead of using `bd` commands | NEVER read `.beads/*.jsonl` files directly. Always use `bd ready`, `bd show`, `bd list`, etc. AGENTS.md is explicit about this. |
| 2026-02-13 | self | `grep_search` query starting with `--output` was parsed as an rg flag and failed | Escape leading hyphens in grep patterns (e.g. `\\-\\-output`) or use fixed-string-safe patterns that don't start with `-`. |

## User Preferences
- Uses `bd comments add <id> "text"` not `bd note add` for beads
- Follow AGENTS.md workflow strictly: claim bead, do work, run tests, request review before commit
- Present review/diff after EACH bead is completed, before moving to the next one
- NEVER start the next bead until user explicitly says to — stop and wait after push

## Patterns That Work
- (accumulate here as you learn them)

## Patterns That Don't Work
- (approaches that failed and why)

## Domain Notes
- Project uses uv for Python deps, npm for UI deps
- Tests: pytest (Python), Vitest (UI)
- Linting: Ruff (Python), ESLint (TypeScript)
- `make test` runs all Python tests, `cd ui && npm run test:run` for UI tests
