#!/bin/sh
set -e

# Navigate into project directory
cd shoptech

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn shoptech.wsgi:application --bind 0.0.0.0:8000
