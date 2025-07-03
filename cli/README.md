# Document Server CLI

A powerful command-line interface with **terminal-based session management** and **directory navigation**.

## Key Features

- **Terminal-based Sessions**: Each terminal maintains its own independent session
- **Directory Navigation**: `cd`, `pwd`, `ls` commands like traditional file systems
- **Context-Aware Operations**: `upload`, `mkdir`, `delete` use current directory by default
- **Folder Management**: Create, navigate, and manage folders
- **Smart File Search**: Commands prioritize current directory, fall back to global search
- **Rich Terminal UI**: Beautiful interface with colors, icons, and progress indicators

## Quick Start

### Native CLI (Recommended for development)
```bash
cd cli
pip install -r requirements.txt
python main.py
```

### Docker CLI (Recommended for production)
```bash
# From project root
./run-cli.sh

# Or with docker-compose directly
docker-compose run --rm cli
```

## Commands

### Authentication
| Command | Description |
|---------|-------------|
| `login <username> <password>` | Login to the server |
| `register <username> <email> <password> [grade]` | Register new account |
| `logout` | Logout and clear session |
| `status` | Show current login status |

### File Operations
| Command | Description |
|---------|-------------|
| `list [folder_name]` | List all files or files in specific folder |
| `ls [folder_name]` | List files and folders in specific folder (alias for list) |
| `upload <file_path>` | Upload a file (to current directory by default) |
| `download <filename> [output_path]` | Download a file by filename |
| `delete <filename>` | Delete a file (from current directory by default) |

### Folder Operations
| Command | Description |
|---------|-------------|
| `mkdir <folder_name> [parent_id]` | Create a new folder (in current directory by default) |
| `folders` | List all folders |
| `rmdir <folder_name>` | Delete a folder by name |
| `tree` | Show folder tree structure |
| `cd <folder_name>` | Change current folder context |
| `pwd` | Show current folder path |
| `mv <filename> <folder_name>` | Move file to different folder |

### Session Management
| Command | Description |
|---------|-------------|
| `sessions` | List all terminal sessions |
| `help` | Show help message |
| `exit` | Exit the CLI |

## Example Workflow

```bash
# Start CLI
./run-cli.sh

# Login and explore
doccli (admin)> login admin admin123
doccli (admin)> list
doccli (admin)> tree

# Create and navigate folders
doccli (admin)> mkdir documents
doccli (admin)> cd documents
doccli (admin)> pwd
Current directory: /documents

# Upload files to current directory
doccli (admin)> upload /path/to/report.pdf
Uploading to current directory: documents
File uploaded successfully!

# List contents with folders
doccli (admin)> ls
Contents of current directory 'documents':
  📁 projects/ (ID: 4)
  📄 report.pdf - Available

# Navigate and manage
doccli (admin)> cd projects
doccli (admin)> mkdir 2024
doccli (admin)> mv report.pdf 2024/
doccli (admin)> list
Contents of current directory 'projects':
  📁 2024/ (ID: 5)
  📄 report.pdf - Available

# Clean up and exit
doccli (admin)> logout
Logged out successfully!
Current directory reset to root
```

## Terminal Session Management

### Independent Sessions
- Each terminal window maintains its own session
- Multiple users can be logged in simultaneously
- Sessions are automatically saved and restored per terminal
- Directory state resets to root on logout/exit

### Session Files
```
cli/sessions/
├── terminal_a1b2c3d4.session  # Terminal 1 session
├── terminal_e5f6g7h8.session  # Terminal 2 session
└── terminal_i9j0k1l2.session  # Terminal 3 session
```

### Multi-Terminal Example
**Terminal 1** (admin):
```bash
doccli (admin)> login admin password123
doccli (admin)> cd documents
doccli (admin)> upload file1.pdf
```

**Terminal 2** (user1):
```bash
doccli (user1)> login user1 password456
doccli (user1)> cd work
doccli (user1)> upload file2.pdf
```

## Installation

### Native CLI
```bash
cd cli
pip install -r requirements.txt
chmod +x main.py

# Optional: Install globally
./install.sh
```

### Docker CLI
```bash
# From project root (recommended)
./run-cli.sh

# Or with docker-compose directly
docker-compose run --rm cli

# Or from CLI directory
cd cli
./run.sh
```

## Configuration

### Environment Variables
- `DOCUMENT_SERVER_URL`: Backend server URL (default: `http://localhost:5001`)

### Requirements
- Python 3.7+ (for native CLI)
- Docker and Docker Compose (for Docker CLI)
- Backend service running (`docker-compose up -d`)

## Troubleshooting

### Common Issues
1. **"Please login first" after login**: Ensure backend is running
2. **Upload fails**: Check file path and backend status
3. **Session not persisting**: Verify `cli/sessions/` directory permissions
4. **Docker CLI not working**: Make sure backend services are running

### Session Commands
- `sessions` - View all active terminal sessions
- `logout` - Clear current session
- `status` - Check login status

## Project Structure
```
cli/
├── main.py              # Main CLI entry point
├── core/
│   ├── client.py        # Thin orchestrator
│   ├── session.py       # Authentication & sessions
│   ├── files.py         # File operations
│   ├── folders.py       # Folder operations
│   └── commands.py      # Command definitions
├── sessions/            # Session storage
├── requirements.txt     # Dependencies
├── run.sh              # Native CLI runner
└── install.sh          # Installation script

# Root level
run-cli.sh              # Docker CLI runner (uses docker-compose)
``` 