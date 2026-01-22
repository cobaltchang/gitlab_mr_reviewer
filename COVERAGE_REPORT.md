Coverage report notes
=====================

Summary of steps taken to reach 100% coverage for `src` (excluding deprecated modules):

- Added supplementary tests to exercise exception and edge branches.
- Excluded deprecated modules from coverage via `.coveragerc`.
- Ensured subprocess and filesystem paths in tests use timeouts and `tmp_path` fixtures to avoid hangs.
- Updated `CONTRIBUTING.md` with coverage policy and validation commands.

Final result: `114` tests passed and coverage for `src` (with omit) is `100%` in local runs.

Test summary:

- `pytest`: 114 passed, 2 warnings
- `coverage`: 100.00% for `src`

Notes:
- Warnings observed during test runs (e.g., urllib3 deprecation) are unrelated to business logic; consider upgrading dependencies to silence them.
- CI integration to enforce coverage threshold is recommended.
