FROM python:3.12-slim

# Keep image lean and predictable
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create a non-root user and switch to it
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

# APP_VERSION is read by the app at runtime via app/config.py.
# Override at `docker run` time to demonstrate a rolling deployment, e.g.:
#   docker run -e APP_VERSION=1.1.0 -p 8000:8000 task-manager
ENV APP_VERSION=1.0.0

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
