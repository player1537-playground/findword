# Stage 1: Base image with code only (tagged as 'latest')
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies (minimal for SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install hypercorn && \
    pip install -e .

# Copy application code
COPY src/ ./src/
COPY manage.py .

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/logs /app/data

# Create non-root user
RUN useradd -m -u 1000 django && \
    chown -R django:django /app

USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/', timeout=5)" || exit 1

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (using hypercorn ASGI server)
CMD ["hypercorn", "--bind", "0.0.0.0:8000", "--workers", "4", "core.asgi:application"]


# Stage 2: Image with data included (tagged as 'latest-withdata')
FROM base AS withdata

# Switch to root to copy data
USER root

# Copy data directory (SQLite DB, FastText models, etc.)
COPY --chown=django:django data/ /app/data/

# Switch back to non-root user
USER django
