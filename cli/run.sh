#!/bin/bash

# Document Server CLI Runner Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the CLI
python3 "$SCRIPT_DIR/main.py" "$@" 