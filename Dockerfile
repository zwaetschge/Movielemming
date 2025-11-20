# MediaCleaner Dockerfile
# Multi-stage build for optimal image size

# Stage 1: Frontend build (placeholder for Phase 3)
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend

# Copy frontend package files
# COPY frontend/package*.json ./
# RUN npm ci

# Copy frontend source and build
# COPY frontend/ ./
# RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg installation
RUN ffmpeg -version && ffprobe -version

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/app ./app

# Create necessary directories
RUN mkdir -p /app/data /app/public/thumbnails /data

# Copy frontend build (when available)
# COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data
ENV THUMBNAIL_DIR=/app/public/thumbnails
ENV DATABASE_PATH=/app/data/mediacleaner.db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
