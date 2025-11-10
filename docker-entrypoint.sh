#!/bin/bash
set -e

echo "Starting FindWord application..."

# Wait a moment for any filesystem operations to complete
sleep 1

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting application server..."

# Execute the main command (passed as arguments to this script)
exec "$@"
