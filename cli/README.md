# Document Server CLI

A command-line interface for the Document Server platform with **terminal-based session management**.

## Key Features

- **Terminal-based Sessions**: Each terminal window maintains its own independent session
- **Multi-User Support**: Multiple users can be logged in simultaneously in different terminals
- **Session Persistence**: Sessions are automatically saved and restored per terminal
- **Rich Terminal UI**: Beautiful interface with progress indicators and colored output
- **File Operations**: Upload, download, list, and delete files
- **User Management**: Register new accounts and manage authentication

## Installation

### Option 1: Native Installation (Recommended)

1. **Install dependencies**:
   ```bash
   cd cli
   pip install -r requirements.txt
   ```

2. **Install globally** (optional):
   ```bash
   ./install.sh
   ```

### Option 2: Docker Installation

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d cli
   ```

2. **Use the Docker CLI**:
   ```bash
   ./cli-docker.sh
   ```

## Usage

### Starting the CLI

**Native CLI**:
```bash
# If installed globally
doccli

# Or run directly
python cli/main.py
```

**Docker CLI**:
```bash
./cli-docker.sh
```

### Terminal-Based Session Management

Each terminal window maintains its own independent session. This means:

- **Multiple Users**: Different users can be logged in simultaneously in different terminals
- **Session Isolation**: Each terminal's session is completely separate
- **Automatic Persistence**: Sessions are saved per terminal and restored automatically
- **No Conflicts**: No need to logout from one terminal to login in another

### Basic Commands

#### Authentication
```bash
# Login to the system
login admin password123

# Register a new account
register newuser user@example.com password123

# Logout from current session
logout

# Check current status
status
```

#### File Operations
```bash
# Upload a file
upload /path/to/document.pdf

# List all files
list

# Download a file
download document.pdf

# Download with custom output path
download document.pdf /tmp/my_document.pdf

# Delete a file
delete document.pdf
```

#### Session Management
```bash
# List all active terminal sessions
sessions

# Show help
help

# Exit the CLI
exit
```

### Multi-Terminal Usage Example

**Terminal 1** (User: admin):
```bash
$ doccli
doccli (a1b2c3d4)> login admin password123
Login successful! Welcome, admin
Terminal Session ID: a1b2c3d4

doccli (a1b2c3d4)> upload document1.pdf
File uploaded successfully! File ID: 123
```

**Terminal 2** (User: user1):
```bash
$ doccli
doccli (e5f6g7h8)> login user1 password456
Login successful! Welcome, user1
Terminal Session ID: e5f6g7h8

doccli (e5f6g7h8)> upload document2.pdf
File uploaded successfully! File ID: 124
```

**Terminal 3** (Check sessions):
```bash
$ doccli
doccli (i9j0k1l2)> sessions
Active Terminal Sessions (2):
  • admin (Terminal: a1b2c3d4, PID: 12345)
    Last active: 2024-01-15T10:30:00
  • user1 (Terminal: e5f6g7h8, PID: 12346)
    Last active: 2024-01-15T10:35:00
```

## Session Files

Sessions are stored in `cli/sessions/` with the following structure:
```
cli/sessions/
├── terminal_a1b2c3d4.session  # Terminal 1 session (admin)
├── terminal_e5f6g7h8.session  # Terminal 2 session (user1)
└── terminal_i9j0k1l2.session  # Terminal 3 session (not logged in)
```

Each session file contains:
- Authentication cookies
- Username
- Terminal session ID
- Process ID
- Timestamp

## Configuration

### Environment Variables

- `DOCUMENT_SERVER_URL`: Backend server URL (default: `http://localhost:5001`)

### Backend Requirements

Make sure the Document Server backend is running:
```bash
docker-compose up -d backend
```

## Troubleshooting

### Common Issues

1. **"Please login first" after login**:
   - Make sure the backend service is running
   - Check that the session was saved properly

2. **Upload fails with 400 error**:
   - Verify the file path is correct
   - Check file permissions
   - Ensure the backend is running

3. **Session not persisting**:
   - Check that the `cli/sessions/` directory exists
   - Verify write permissions

### Session Management

- **View all sessions**: Use `sessions` command
- **Clear a session**: Use `logout` command
- **Switch users**: Login in a new terminal window
- **Session cleanup**: Sessions are automatically cleaned up on logout

## Development

### Project Structure
```
cli/
├── main.py              # Main CLI entry point
├── core/
│   ├── client.py        # DocumentServerCLI class
│   └── commands.py      # Click-based commands (legacy)
├── sessions/            # Session storage directory
├── requirements.txt     # Python dependencies
├── install.sh          # Global installation script
└── README.md           # This file
```

### Running Tests
```bash
cd cli
python -m pytest tests/
```

## License

This project is part of the Document Server platform. 