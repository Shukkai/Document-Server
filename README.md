<!-- # Document Center -->
<p align="center">
  <img src="./assets/icon.png" width="80" alt="Document Center Icon">
</p>

<h1 align="center">Document Center</h1>

*A unified platform to upload, manage, and review enterprise documents.*

![image](./assets/arch.png)

---

## Overview

**Document Center** is a centralized platform designed for enterprises to manage diverse technical and production documents. It enables users to upload, edit, and audit files within an integrated and secure environment. It ensures that document publishing adheres to review and approval workflows, which is critical for industries with compliance or traceability requirements.

## Tech Stack

| Layer        | Technology                          |
|-------------|--------------------------------------|
| Frontend     | Vue 3, Vite, Axios                   |
| Backend      | Flask, Flask-Login, SQLAlchemy       |
| Database     | MySQL 8                              |
| Cache        | Redis                                |
| Auth         | Session-based login, Google OAuth    |
| Monitoring   | Prometheus, Grafana                  |
| CLI          | Python Click, Rich                   |
| CI/CD        | GitHub Actions                       |
| Deployment   | Docker, Docker Compose, Kubernetes   |

## Features

### Authentication

- User registration and login with session support
- Password reset via email token
- Change password while logged in
- Role-based access: admin and non-admin users

### File Management

- Upload, list, and download files (per-user scoped)
- File metadata tracking: filename, MIME type, path, upload time
- File size limit enforcement (default: 256 MB)

### Frontend (Vue 3 + Vite)

- Upload/download UI with dynamic links
- Password reset prompt
- Axios-based API integration
- Responsive layout with a simple navigation bar

### Backend (Flask)

- RESTful API using Flask and Flask-Login
- File upload handling with `werkzeug`
- Token-based password reset support
- MySQL integration using SQLAlchemy
- Redis caching for improved performance
- CORS support with credentials

### CLI Tool

- **Terminal-based session management** with independent sessions per terminal
- **Directory navigation** with `cd`, `pwd`, `ls` commands like traditional file systems
- **Context-aware operations** - upload, mkdir, delete use current directory by default
- **Folder management** - create, list, delete, and navigate folders
- **File operations** - upload, download, list, delete with smart search
- **Rich terminal UI** with progress indicators and formatted output
- **Interactive mode** with built-in help system
- **Docker integration** for easy deployment

### Database (MySQL)

- Runs in Docker with persistent volume for data
- Auto-initialized by the backend (`init_db.py`)
- Accessible on host port `3307` (container port `3306`)

### Caching (Redis)

- High-performance caching layer for frequently accessed data
- Automatic cache invalidation on data changes
- Reduces database load and improves response times
- Cached endpoints: folders, public files, and more
- Health monitoring and cache management endpoints

### Monitoring (Prometheus & Grafana)

- Real-time metrics exposed via `/metrics` endpoint (Flask + Prometheus)
- Prometheus scrapes metrics and Grafana dashboard for visualizing:
  - API usage statistics
  - Upload/download activity
  - System health (via Docker container stats)

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Running

1. **(Optional)** To enable Google OAuth login, create a `.env` file in the `./backend` directory with the following content:

```bash
cd ./backend
cp .env.sample .env
```

2. Build and start the services:

- Docker:
```bash
docker-compose up --build
```

- k8s:
```bash
cd k8s
./start_k8s.sh
```

3. Access the application:
  - Docker: [http://localhost:8080](http://localhost:8080)
  - k8s: [http://localhost](http://localhost)

## CLI Usage

The Document Center includes a powerful command-line interface with terminal-based session management and directory navigation.

### Quick Start

**Native CLI (Recommended for development)**:
```bash
cd cli
pip install -r requirements.txt
python main.py
```

**Docker CLI (Recommended for production)**:
```bash
# From project root
./run-cli.sh

# Or with docker-compose directly
docker-compose run --rm cli
```

### Key Features

- **Terminal Sessions**: Independent sessions per terminal, multiple users simultaneously
- **Directory Navigation**: `cd`, `pwd`, `ls` commands like traditional file systems
- **Context-Aware Operations**: `upload`, `mkdir`, `delete` use current directory by default
- **Folder Management**: Create, navigate, and manage folders
- **Smart Search**: Commands prioritize current directory, fall back to global search
- **Rich UI**: Beautiful terminal interface with colors, icons, and progress indicators

### Essential Commands

| Category | Commands |
|----------|----------|
| **Auth** | `login`, `register`, `logout`, `status` |
| **Files** | `list`/`ls`, `upload`, `download`, `delete` |
| **Folders** | `mkdir`, `cd`, `pwd`, `rmdir`, `tree`, `mv` |
| **Session** | `sessions`, `help`, `exit` |

### Example Workflow

```bash
# Start CLI
./run-cli.sh

# Login and explore
doccli (admin)> login admin admin123
doccli (admin)> mkdir documents
doccli (admin)> cd documents
doccli (admin)> upload report.pdf
doccli (admin)> ls
Contents of current directory 'documents':
  📄 report.pdf - Available
```

For detailed CLI documentation, see [cli/README.md](cli/README.md).
