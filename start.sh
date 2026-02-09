#!/bin/bash
set -e

echo "=== Jobper Startup Script ==="
echo "PORT: $PORT"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'YES' || echo 'NO')"
echo "JWT_SECRET set: $([ -n "$JWT_SECRET" ] && echo 'YES' || echo 'NO')"

echo "Starting Gunicorn on port $PORT..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5001}" \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    "app:create_app()"
