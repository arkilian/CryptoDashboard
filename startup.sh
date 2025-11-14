#!/usr/bin/env bash
set -euo pipefail

# Resolve port from Azure envs or default
PORT_TO_USE="${PORT:-${WEBSITES_PORT:-8000}}"

echo "Starting Streamlit on port ${PORT_TO_USE}"

# Ensure we run from repo root
cd "$(dirname "$0")"

# Prevent Streamlit from trying to open a browser
export BROWSER=none

# Launch Streamlit with settings suitable for Azure App Service
exec streamlit run app.py \
  --server.port "${PORT_TO_USE}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false
