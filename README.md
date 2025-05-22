# Document-Server

Document Center is a full-stack web application that allows users to upload, manage, and download various file types, including images and documents. It is built with a Vue.js frontend, a Flask backend, and a MySQL database, all containerized via Docker and deployable on Kubernetes (K3d).

## Features

### Deployment
- Docker Compose support for local development
- Kubernetes manifests for K3d deployment
- Production-ready Dockerfiles for frontend and backend
- Optional load balancer and service discovery via Ingress

### Backend (Flask)
- RESTful API to upload, list, and download files
- Stores file metadata (filename, mimetype, path, timestamp)
- Configurable MySQL database connection
- Supports all common file types (images, documents, etc.)
- Secure and minimal service container

### Frontend (Vue 3 + Vite)
- Modern UI for uploading and listing files
- Download support with dynamic file links
- Axios integration with backend API
- Responsive layout with navigation header
- Dockerized with Nginx for production

### Database (MySQL 8)
- Runs in Docker with environment configuration
- Uses a persistent volume for file and schema durability
- Automatically initialized by the backend on startup

## Project Structure
Document-Center/
├── backend/               # Flask application
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              # Vue 3 application
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── Dockerfile
├── k8s/                   # Kubernetes manifests
│   ├── mysql-deployment.yaml
│   ├── backend-deployment.yaml
│   └── frontend-deployment.yaml
├── docker-compose.yml
└── README.md
## Getting Started

### Prerequisites
- Docker and Docker Compose
- (Optional) `k3d` and `kubectl` for Kubernetes setup

### Running Locally (Docker Compose)

    1. Build and start services:
    docker-compose up --build
	2.	Access the application:
	•	Frontend: http://localhost:5173
	•	Backend API: http://localhost:5001

Running on K3d (Kubernetes)
	1.	Create a local Kubernetes cluster:
    k3d cluster create doc-center --agents 2 --port "5173:80@loadbalancer"
    2.	Build and import Docker images:
    docker build -t doccenter-backend ./backend
    docker build -t doccenter-frontend ./frontend
    k3d image import doccenter-backend doccenter-frontend -c doc-center
    3.	Apply Kubernetes manifests:
    kubectl apply -f k8s/
    4.	Access via:
	•	http://localhost:5173
