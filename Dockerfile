# =============================================================================
# Jobper v5.0 — Multi-stage Dockerfile
# Stage 1: Build React frontend
# Stage 2: Python backend + serve built frontend
# =============================================================================

# --- Stage 1: Build frontend ---
FROM node:20-slim AS frontend
WORKDIR /dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# --- Stage 2: Python backend ---
FROM python:3.11-slim

# System deps for psycopg2, lxml, health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libxml2-dev libxslt1-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# PyTorch CPU-only first (saves ~5GB vs full PyTorch with CUDA)
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend /dashboard/dist ./dashboard/dist

# Create directories
RUN mkdir -p uploads/comprobantes .cache/huggingface

# Environment - set BEFORE model download so it goes to the right place
ENV PORT=5001
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

# Pre-download the sentence-transformers model during build (avoids timeout in production)
RUN python -c "from sentence_transformers import SentenceTransformer; print('Downloading model...'); SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('Model ready')" || echo "Model preload skipped"

# Expose port
EXPOSE 5001

# Make startup script executable
RUN chmod +x start.sh

# Default command
CMD ["./start.sh"]
