#!/usr/bin/env bash
set -euo pipefail

# Diagnostic logging
echo "==== Startup $(date -u) UTC ===="
echo "Working dir: $(pwd)"
echo "Listing root:"; ls -1 || true
echo "Python version:"; python --version || true
echo "Env PORT=$PORT WEBSITES_PORT=$WEBSITES_PORT"

# Resolve port from Azure envs or default
PORT_TO_USE="${PORT:-${WEBSITES_PORT:-8000}}"

echo "Starting Streamlit on port ${PORT_TO_USE}"; echo

# Ensure we run from repo root
cd "$(dirname "$0")"

# Prevent Streamlit from trying to open a browser
export BROWSER=none

# Launch Streamlit with settings suitable for Azure App Service
python -m streamlit run app.py \
  --server.port "${PORT_TO_USE}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false || {
    echo "Streamlit exited with code $?" >&2
    exit 1
  }
