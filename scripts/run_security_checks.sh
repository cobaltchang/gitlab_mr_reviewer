#!/usr/bin/env bash
set -euo pipefail

# Local helper: generate SBOM and run pip-audit against requirements
REQ=${1:-requirements.txt}
DEVREQ=${2:-dev-requirements.txt}

echo "Creating temp venv .tmp_venv"
python -m venv .tmp_venv
source .tmp_venv/bin/activate
pip install --upgrade pip
if [ -f "$DEVREQ" ]; then pip install -r "$DEVREQ"; fi
pip install cyclonedx-bom pip-audit || true

echo "Generating SBOM -> docs/sbom.json"
cyclonedx-py requirements "$REQ" -o docs/sbom.json || true

echo "Running pip-audit -> docs/pip_audit_requirements.json"
pip-audit -r "$REQ" -f json -o docs/pip_audit_requirements.json || true

echo "Done. Artifacts: docs/sbom.json docs/pip_audit_requirements.json"
