# GitLab MR Reviewer - AI Agent Instructions

## Test Coverage

This project enforces strict test coverage requirements for core logic.

- Scope: the `src` directory (deprecated `src/worktree/` is omitted via `.coveragerc`).
- Target: **100%** coverage for `src`.
- When adding or modifying code, add/update tests to maintain coverage.

Validation (local):
```bash
# terminal summary
pytest tests/ --cov=src --cov-report=term-missing --timeout=10

# html report
pytest tests/ --cov=src --cov-report=html --timeout=10
open htmlcov/index.html
```

Keep `.coveragerc` committed in the repository so CI and local runs are consistent. If a module is intentionally omitted (e.g. deprecated code), document the reasoning in the PR.

## Commit Practice

When making changes, prefer small, focused commits so each change is reviewable and reversible:

- Make one logical change per commit (code change, test, docs) rather than batching unrelated files.
- Commit frequently during multi-step work and push intermediate checkpoints to feature branches.
- Include a concise commit message describing the intent (e.g. `docs: add coverage policy`, `chore: update .coveragerc`).
- When omitting files from coverage (via `.coveragerc`), include a note in the PR explaining why.

This helps reviewers and CI trace why coverage or behavior changed.

## Commit Checks

To ensure repository quality, every commit should run the test suite and verify coverage is 100% for `src` before committing.

Recommended local command (fails if coverage < 100%):
```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100
```

Suggested lightweight `pre-commit` hook (place in `.git/hooks/pre-commit` and make executable):
```bash
#!/bin/sh
echo "Running tests and coverage check..."
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100 -q
status=$?
if [ $status -ne 0 ]; then
   echo "Tests or coverage failed. Commit aborted." >&2
   exit $status
fi
```

Alternatively, use the `pre-commit` framework or CI pipeline to enforce this requirement server-side (recommended for teams).

## Project Overview

Python CLI tool for automated GitLab MR scanning and local code review setup. Creates isolated `git clone --single-branch` copies for each MR, enabling parallel review workflows without modifying the primary repository.

**Key difference from worktrees**: Uses fresh clones (simpler, no force-push issues) instead of git worktree refs.

## Architecture

### Core Components

1. **Config** ([src/config.py](src/config.py)): Environment-driven settings
   - Required: `GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_PROJECTS_FILE` or `GITLAB_PROJECTS`
   - Optional: `REVIEWS_PATH` (default `~/GIT_POOL/reviews`), `STATE_DIR`, `LOG_LEVEL`, `API_RETRY_COUNT`
   - Always expand paths with `Path().expanduser()` for `~` support

2. **GitLabClient** ([src/gitlab_/client.py](src/gitlab_/client.py)): `python-gitlab` wrapper
   - Methods: `get_project()`, `get_merge_requests()`, `get_mr_details()`
   - Converts API responses to `MRInfo` dataclass (defined in [src/gitlab_/models.py](src/gitlab_/models.py))

3. **MRScanner** ([src/scanner/mr_scanner.py](src/scanner/mr_scanner.py)): Scanning & filtering engine
   - `scan(projects, exclude_wip=True, exclude_draft=True)` returns `List[ScanResult]`
   - `_filter_mrs()` handles multi-stage filtering (WIP, draft flags)

4. **StateManager** ([src/state/manager.py](src/state/manager.py)): Dual storage (SQLite + JSON)
   - SQLite for production queries, JSON for debugging
   - Tracks MR states and scan history
   - Idempotent: uses `CREATE TABLE IF NOT EXISTS`

5. **CloneManager** ([src/clone/manager.py](src/clone/manager.py)): MR clone lifecycle
   - `create_clone(mr_info)` creates `reviews/<project_slug>/<iid>/` with `--single-branch`
   - Deletes existing clone before re-cloning to ensure fresh state
   - Saves `.mr_info.json` metadata in each clone

6. **Main CLI** ([src/main.py](src/main.py)): Click-based interface
   - Commands: `scan`, `list-clones`, `clean-clone`
   - Global component initialization in `init_app()` (called by each command)

### Data Flow

```
Config.from_env() 
  → GitLabClient.get_merge_requests() 
    → MRScanner._filter_mrs()
      → StateManager.save_mr_state()
        → CloneManager.create_clone()
```

## Key Patterns

### Exception Hierarchy
Use custom exceptions from [src/utils/exceptions.py](src/utils/exceptions.py):
- `ConfigError`: Invalid/missing config
- `GitLabError`: API failures
- `CloneError`: Clone operation failures (alias: `WorktreeError` for backwards compatibility)
- `StateError`: Database/JSON persistence failures
- `GitError`: Git command execution failures

**Pattern**: Catch specific exceptions, log context, re-raise or handle appropriately.

### Global Component Initialization
[src/main.py](src/main.py) uses module-level globals initialized in `init_app()`:
```python
config: Optional[Config] = None
gitlab_client: Optional[GitLabClient] = None
mr_scanner: Optional[MRScanner] = None
state_manager: Optional[StateManager] = None
clone_manager: Optional[CloneManager] = None
```
Each Click command calls `init_app()` before using components. This avoids circular imports but requires careful init order.

### Single-Branch Clone Strategy
[src/clone/manager.py](src/clone/manager.py) uses:
```bash
git clone -b <source_branch> --single-branch <repo_url> <path>
```
Benefits: No need for primary repo, handles force-pushes by re-cloning, full isolation per MR.

### Dual Storage
[src/state/manager.py](src/state/manager.py) supports both:
- **SQLite**: Structured queries, production use
- **JSON**: Human-readable debugging
Database schema initialized on first run with idempotent operations.

## Development Workflow

### Test Commands (TDD Required)
```bash
pytest                              # Run all tests
pytest tests/test_config.py        # Specific module
pytest --cov=src                   # Coverage report
```
Test patterns: `monkeypatch` for env vars, `tmp_path` for file ops, `mocker` for API stubs.

### Local Execution
```bash
python -m src.main scan --dry-run
python -m src.main scan --exclude-wip --exclude-draft
python -m src.main list-clones
python -m src.main clean-clone --iid 123 --project <project>
```

### Priority Files to Understand
1. [spec.md](spec.md): Complete requirements and design decisions
2. [CONTRIBUTING.md](CONTRIBUTING.md): TDD workflow and code structure rules
3. [src/config.py](src/config.py): Configuration system
4. [src/main.py](src/main.py): Component orchestration

## Cross-Component Communication

- **GitLabClient → StateManager**: Store MR state after scanning for update tracking
- **MRScanner → StateManager**: Check existing state before filtering to avoid redundant API calls
- **StateManager → CloneManager**: Get stored MR info before creating clones
- **All components → Logger**: Central logging via [src/logger/__init__.py](src/logger/__init__.py)

## Common Pitfalls

- **Unexpanded paths**: Always use `Path().expanduser()` for `~` support in config
- **Forgotten state sync**: StateManager must be initialized before scanning
- **Ignoring draft flag**: GitLab versions differ; check both `draft` and `work_in_progress` attributes
- **Direct subprocess calls**: Use CloneManager methods, not raw `git` commands elsewhere
- **Missing error context**: Include project/MR IID in log messages for debugging
- **Not updating StateManager**: Any persistent data changes need StateManager updates

## Adding Features

1. **Write tests first** (TDD): Create failing test in `tests/test_*.py`
2. **Implement in appropriate module** (single responsibility)
3. **Persist if needed**: Update StateManager for new state tracking
4. **CLI command**: Add Click command in [src/main.py](src/main.py) if user-facing
5. **Document**: Update [spec.md](spec.md) with design rationale
