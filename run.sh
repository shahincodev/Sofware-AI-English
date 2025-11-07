# Sofware-AI - Run script for Unix shells
# This script creates a virtualenv named .venv, installs dependencies,
# creates it from .env.example if it doesn't exist, and then runs the main program.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Specify the Python command (I prefer python3)
PYTHON_CMD=python3
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  PYTHON_CMD=python
fi

# Create virtualenv if it doesn't exist
if [ ! -f ".venv/bin/python" ]; then
  echo "Creating virtual environment .venv..."
  "$PYTHON_CMD" -m venv .venv
fi

# Activate
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Using Python: $(which python)"

# Upgrade pip and install requirements if present
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  echo "Installing requirements from requirements.txt..."
  python -m pip install -r requirements.txt
fi

# If the .env.example file does not exist, copy it to .env.
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created .env from .env.example. Please edit .env and add real API keys before use."
  else
    echo "Warning: .env not found and .env.example not present."
  fi
fi

# Create the required directories
mkdir -p "$SCRIPT_DIR/data/logs/cache"

# Run the application (forward arguments)
exec python main.py "$@"
