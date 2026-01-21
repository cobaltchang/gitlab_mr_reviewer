Coverage report notes
=====================

Summary of steps taken to reach 100% coverage for `src` (excluding deprecated `src/worktree/`):

- Added supplementary tests to exercise exception and edge branches.
- Excluded deprecated `src/worktree/` from coverage via `.coveragerc`.
- Ensured subprocess and filesystem paths in tests use timeouts and `tmp_path` fixtures to avoid hangs.
- Updated `CONTRIBUTING.md` with coverage policy and validation commands.

Final result: coverage for `src` (with omit) reached 100% in local runs.

Notes:
- Warnings observed during test runs (e.g., urllib3 deprecation) are unrelated to business logic; consider upgrading dependencies to silence them.
- CI integration to enforce coverage threshold is recommended.
