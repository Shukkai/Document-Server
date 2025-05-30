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
- Environment variables:
  - DATABASE_URL=mysql+pymysql://flaskuser:flaskpass@mysql/cloud_docs
  - SECRET_KEY=dev-key # Default secret key, consider changing for production

### Database (MySQL 8)

- Runs in Docker with persistent volume for data
- Auto-initialized by the backend (`init_db.py`)
- Default credentials (from `docker-compose.yml`):
  - MYSQL_ROOT_PASSWORD: root
  - MYSQL_DATABASE: cloud_docs
  - MYSQL_USER: flaskuser
  - MYSQL_PASSWORD: flaskpass
- Accessible on host port `3307` (container port `3306`)

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Running Locally

1. Create a `.env` file in the `./backend` directory with the following content:

```env
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
```

2. Build and start the services:

```bash
docker-compose up --build
```

3. Access the application:

- Frontend: http://localhost:8080  
- Backend: http://localhost:5001  
- phpMyAdmin (Database Admin): http://localhost:8081 (Use `mysql` as host, `root` as user, and `root` as password)  
- add a admin/non-admin users for testing
