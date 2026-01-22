**Security Automation & Remediation Process (Reusable)**

Overview
- This document describes a repeatable, reusable security scan and remediation workflow suitable for this project and other Python projects.

Goals
- Continuously detect vulnerable dependencies and record SBOMs.
- Open actionable artifacts (issues, PRs) for maintainers.
- Keep runtime `requirements.txt` separate from dev tooling `dev-requirements.txt`.

Core components
- Reusable workflow: `.github/workflows/security-scan-reusable.yml` — callable from other repos via `workflow_call`.
- PR-level checks: `.github/workflows/pr-security-check.yml` — runs on pull requests.
- Local scripts: `scripts/run_security_checks.sh` and `scripts/generate_sbom.sh` for developers.
- Templates: PR template for security upgrades and an issue template for reported vulnerabilities.

Process (high level)
1) Detection
   - Scheduled runs call the reusable workflow with `workflow_dispatch` or `schedule`.
   - `pip-audit` scans declared runtime dependencies and outputs JSON.
   - `cyclonedx-py` generates `sbom.json` for auditing.
2) Triage
   - The workflow creates a GitHub Issue summarizing findings.
   - Assign appropriate owners / `CODEOWNERS` for triage.
3) Remediation
   - For runtime vulnerabilities: create a per-package branch and Draft PR using the repository policy.
   - For dev-only tools: update `dev-requirements.txt` directly and run CI.
4) Verification
   - PRs must pass `pr-security-check` (tests + pip-audit + SBOM generation) before merging.
5) Release & Audit
   - Attach the final `sbom.json` to releases or store under `sbom/` for audited builds.

How to reuse in another repository
1) Copy `.github/workflows/security-scan-reusable.yml` to the target repo.
2) Configure a scheduled workflow that calls it, for example:

```yaml
on:
  schedule:
    - cron: '0 3 * * 1'

jobs:
  call-security:
    uses: <owner>/<repo>/.github/workflows/security-scan-reusable.yml@main
    with:
      requirements-path: requirements.txt
      dev-requirements-path: dev-requirements.txt
      run-tests: true
      create-prs: false
```

3) Add `pr-security-check.yml` or adapt to your CI matrix for PR verification.

Local developer scripts
- Run full local scan and SBOM generation:

```bash
./scripts/run_security_checks.sh
```

Notes & Best Practices
- Prefer creating small, single-package upgrade PRs for easy rollbacks.
- Keep SBOM generation in CI to avoid noisy commits; commit SBOM only for releases.
- Use `CODEOWNERS` to route security PRs to the right reviewers.
