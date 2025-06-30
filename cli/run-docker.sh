#!/bin/bash

# Simple Docker CLI Runner Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root and run the main Docker CLI script
cd "$PROJECT_ROOT"
./run-cli-docker.sh "$@" 