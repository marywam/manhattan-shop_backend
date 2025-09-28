FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 8000

# Run collectstatic at container startup
CMD python shoptech/manage.py collectstatic --noinput && \
    gunicorn shoptech.wsgi:application --bind 0.0.0.0:8000
