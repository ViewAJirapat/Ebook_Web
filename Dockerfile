# ==============================================================================
# Stage 1: Build Frontend SPA (Vue 3 + Vite + Tailwind CSS)
# ==============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first for efficient layer caching
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source and build production bundle
COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Production Python Backend & Static Asset Serving
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=80 \
    DATA_DIR=/app/data \
    DATABASE_DIR=/app/database \
    DIST_DIR=/app/dist

WORKDIR /app

# Install system dependencies for PyMuPDF and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmupdf-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ /app/backend/

# Copy built frontend dist from Stage 1 into /app/dist
COPY --from=frontend-builder /app/frontend/dist /app/dist

# Expose production port
EXPOSE 80

# Start FastAPI server on configured PORT
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-80}"]
