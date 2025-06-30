#!/bin/bash

# Document Server CLI Installation Script

echo "Installing Document Server CLI..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Make the CLI executable
chmod +x run.sh

# Create symlink to make doccli available globally (optional)
if [ "$1" = "--global" ]; then
    echo "Creating global symlink..."
    # Get the absolute path to the main.py file
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MAIN_PY_PATH="$SCRIPT_DIR/main.py"
    
    # Create the symlink
    sudo ln -sf "$MAIN_PY_PATH" /usr/local/bin/doccli
    echo "CLI installed globally. You can now use 'doccli' from anywhere."
    echo "The CLI is located at: $MAIN_PY_PATH"
else
    echo "CLI installed locally. Use './run.sh' or 'python3 main.py' to run."
fi

echo "Installation complete!" 