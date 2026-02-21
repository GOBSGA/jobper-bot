#!/bin/bash
set -e

echo "=== Jobper Startup Script ==="
echo "PORT: $PORT"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'YES' || echo 'NO')"
echo "JWT_SECRET set: $([ -n "$JWT_SECRET" ] && echo 'YES' || echo 'NO')"

echo "=== Running database migrations ==="
alembic upgrade head && echo "=== Migrations complete ===" || echo "=== Migrations failed (non-fatal) - app will apply missing columns on startup ==="

echo "Starting Gunicorn on port $PORT..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5001}" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    "app:create_app()"
