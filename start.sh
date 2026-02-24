#!/bin/bash
set -e

echo "=== Jobper Startup Script ==="
echo "PORT: $PORT"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'YES' || echo 'NO')"
echo "JWT_SECRET set: $([ -n "$JWT_SECRET" ] && echo 'YES' || echo 'NO')"

echo "=== Running database migrations ==="
if alembic upgrade head; then
  echo "=== Migrations complete ==="
else
  MIGRATION_EXIT=$?
  echo "=== Migrations failed (exit $MIGRATION_EXIT) — app will apply missing columns on startup ==="
fi

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
