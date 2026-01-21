# CVE Triage and Remediation Process

Purpose: provide a deterministic triage process and SLAs aligned with CRA/IEC 62443 expectations.

1. Classification
- Critical: active exploit or remote code execution on default config — SLA: 7 days to patch, 30 days to release fix.
- High: local privilege escalation or data exposure — SLA: 14 days to patch, 45 days to release fix.
- Medium/Low: informational or low-impact — SLA: 90 days.

2. Assignment
- Create a GitHub Issue tagged `security` and assign the security owner.

3. Fix workflow
- Branch `chore/security/upgrade-<pkg>` created with minimal version bump.
- Run CI (tests + security-scan). If CI fails, iterate until green.

4. Disclosure
- Coordinate public disclosure per severity; delay public advisory until fix is available for Critical/High.
