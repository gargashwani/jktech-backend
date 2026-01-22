FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy project files
COPY . .

# Create storage directories
RUN mkdir -p storage/app public/storage

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "main.py"]
