FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy CLI source code
COPY . .

# Make scripts executable
RUN chmod +x run.sh main.py

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCUMENT_SERVER_URL=http://backend:5001

# Create a non-root user
RUN useradd -m -u 1000 cliuser && chown -R cliuser:cliuser /app
USER cliuser

# Default command (can be overridden by docker-compose)
CMD ["python3", "main.py"] 