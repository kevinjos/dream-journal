# Multi-stage build for Django backend
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install dependencies
COPY requirements.txt .
ARG VIRTUAL_ENV=/home/venv
RUN python -m venv ${VIRTUAL_ENV} && \
    . ${VIRTUAL_ENV}/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project and collect static files
COPY . /app
WORKDIR /app

# Collect static files using venv Python
RUN /home/venv/bin/python manage.py collectstatic --noinput --settings=dream_journal.settings

# Production stage using distroless
FROM gcr.io/distroless/python3-debian12:latest

ARG VIRTUAL_ENV=/home/venv

# Copy virtual environment and application code
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder /app /app
WORKDIR /app

# Set PYTHONPATH for Django and venv packages
ENV PYTHONPATH=/app:/home/venv/lib/python3.11/site-packages

# Expose port
EXPOSE 8000

# Run gunicorn using wrapper script with system Python
# PORT environment variable will be handled by run.py
ENTRYPOINT ["/usr/bin/python3.11", "run.py"]
CMD ["--workers", "3", "--timeout", "120", "dream_journal.wsgi:application"]
