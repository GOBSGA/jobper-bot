#!/bin/bash
set -e

echo "=== Jobper Startup Script ==="
echo "PORT: $PORT"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'YES' || echo 'NO')"
echo "JWT_SECRET set: $([ -n "$JWT_SECRET" ] && echo 'YES' || echo 'NO')"

echo "Testing Python import..."
python -c "from app import create_app; app = create_app(); print('Flask app created successfully')"

echo "Starting Gunicorn on port $PORT..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5001}" \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    "app:create_app()"
