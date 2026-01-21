# Security Policy

Responsible disclosure and vulnerability reporting

If you believe you have found a security vulnerability in this project, please report it privately by opening an issue addressed to the maintainers with the prefix `SECURITY:` or send email to security@example.com. Provide steps to reproduce, affected versions, and any PoC you have.

We aim to respond within 3 business days and will provide a remediation timeline. For confirmed critical vulnerabilities, we will coordinate disclosure and provide patches or mitigation guidance.

Automated scanning

This repository runs automatic security scans on push and pull requests (`pip-audit`, `bandit`, and SBOM generation). Pip-audit is configured to fail the job on high severity findings.

Acknowledgements

Thank you to anyone who reports vulnerabilities responsibly. We will credit reporters in release notes unless they request anonymity.
