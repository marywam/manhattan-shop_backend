# Backend (Django)
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Collect static files
RUN python shoptech/manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "shoptech.wsgi:application", "--bind", "0.0.0.0:8000"]
