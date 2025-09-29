#!/bin/sh

# Exit on error
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn shoptech.wsgi:application --bind 0.0.0.0:8000
