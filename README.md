# Document Center

**Document Center** is a full-stack web application that allows users to upload, manage, download, and securely modify files. It is built with a Vue 3 frontend, Flask backend, and MySQL database. The entire stack runs in Docker using Docker Compose for local development.

---

## Features

### Authentication
- User registration and login with session support
- Password reset via email token
- Change password while logged in

### File Management
- Upload, list, and download files
- Files are scoped per user
- Stores filename, mimetype, path, and upload time
- File size limit enforcement (default: 256 MB)

### Frontend (Vue 3 + Vite)
- Upload and download interface with dynamic links
- Password reset prompt
- Axios integration with backend API
- Responsive layout with a simple navigation bar

### Backend (Flask)
- RESTful API using Flask and Flask-Login
- File upload handling with `werkzeug`
- Token-based password reset support
- MySQL integration using SQLAlchemy
- CORS support with credentials

### Database (MySQL 8)
- Runs in Docker with persistent volume for data
- Auto-initialized by the backend

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Running Locally

1. Build and start the services:

```bash
docker-compose up --build
```
2.	Access the application:

•	Frontend: http://localhost:5173
•	Backend: http://localhost:5001
