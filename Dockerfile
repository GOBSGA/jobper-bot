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
RUN npm run build && \
    echo "=== Frontend build complete ===" && \
    ls -la dist/ && \
    echo "=== dist/assets ===" && \
    ls -la dist/assets/ || echo "No assets folder"

# --- Stage 2: Python backend ---
FROM python:3.11-slim

# System deps for psycopg2, lxml, bcrypt, health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libxml2-dev libxslt1-dev libffi-dev curl \
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
RUN echo "=== Verifying frontend in final image ===" && \
    ls -la dashboard/ && \
    ls -la dashboard/dist/ || echo "ERROR: dashboard/dist not found!"

# Create non-root user for security
RUN groupadd -r jobper && useradd -r -g jobper jobper

# Create directories with proper permissions
RUN mkdir -p uploads/comprobantes .cache/huggingface && \
    chown -R jobper:jobper /app

# Environment - set BEFORE model download so it goes to the right place
ENV PORT=5001
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

# Pre-download the sentence-transformers model during build (avoids timeout in production)
# Run as jobper user to ensure cache directory is writable
USER jobper
RUN python -c "from sentence_transformers import SentenceTransformer; print('Downloading model...'); SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('Model ready')" || echo "Model preload skipped"

# Make startup script executable
RUN chmod +x start.sh || true

# Expose port
EXPOSE 5001

# Health check - verify app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run as non-root user
USER jobper

# Default command
CMD ["./start.sh"]
