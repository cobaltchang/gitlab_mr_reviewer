# Security Policy

Responsible disclosure and vulnerability reporting


If you believe you have found a security vulnerability in this project, please report it privately by opening an issue addressed to the maintainers with the prefix `SECURITY:` or send email to security@example.com. Provide steps to reproduce, affected versions, and any PoC you have.

Response targets and SLAs:

- Acknowledge receipt: within 24 hours.
- Initial triage: within 3 business days.
- Critical fix (active exploit / RCE): patch branch within 7 days, release within 30 days.
- High fix (local escalation / data exposure): patch branch within 14 days, release within 45 days.

Automated scanning

This repository runs automatic security scans on push and pull requests (`pip-audit`, `bandit`, and SBOM generation). Pip-audit is configured to fail the job on high severity findings. A weekly scheduled job regenerates SBOM and security reports and uploads artifacts for auditing.

Related documents:

- Incident response: `docs/incident_response.md`
- CVE triage: `docs/cve_triage.md`
- Threat model: `docs/threat-model.md`

Acknowledgements

Thank you to anyone who reports vulnerabilities responsibly. We will credit reporters in release notes unless they request anonymity.
