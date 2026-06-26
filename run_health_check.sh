#!/bin/bash

# Launcher for repo health checks to ensure environment consistency.
# Use this instead of calling python3 directly from n8n.

REPO_ROOT="/home/cbk/qwen-agent-collective"
VENV_PYTHON="$REPO_ROOT/venv/bin/python3"

# Ensure we are in the root directory
cd "$REPO_ROOT" || { echo "Error: Could not cd to $REPO_ROOT"; exit 1; }

# Verify venv exists, if not try to warn (though we already set it up)
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment python not found at $VENV_PYTHON"
    exit 1
fi

# Run the health check using the Venv Python
# We use exec to replace the shell process with the python process, preserving exit codes
exec "$VENV_PYTHON" shared/repo_health.py
