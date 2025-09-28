#!/bin/sh

# Exit on error
set -e

# Run migrations
python shoptech/manage.py migrate --noinput

# Collect static files
python shoptech/manage.py collectstatic --noinput

# Start Gunicorn
gunicorn shoptech.wsgi:application --bind 0.0.0.0:8000
