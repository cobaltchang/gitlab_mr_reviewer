# Incident Response Playbook

Purpose: provide a repeatable set of steps to respond to a reported or detected security incident affecting this project.

1. Triage
- Confirm receipt in issue tracker (private channel) and acknowledge within 24 hours.
- Assign severity (Critical / High / Medium / Low) using impact on confidentiality, integrity, availability.

2. Containment
- For code/CI issues: disable affected workflow or revoke secrets immediately if leaked.
- For dependency CVE: create a prioritized PR to patch or apply mitigation (constraints/rollback).

3. Investigation
- Collect artifacts: `installed.txt`, `pip_audit_report.json`, `sbom.json`, logs.
- Reproduce in isolated environment.

4. Remediation
- Apply patch or upgrade dependency, test, and merge to mainline following PR process.
- Coordinate disclosure timeline if vulnerability is public-facing.

5. Post-incident
- Publish summary (redacted) and lessons learned; rotate affected credentials.
