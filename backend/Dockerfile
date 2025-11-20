# Multi-stage Dockerfile for ADHD Board API

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libusb-1.0-0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source needed for dependency resolution
COPY pyproject.toml ./
COPY app ./app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libusb-1.0-0 \
    curl \
    chromium \
    chromium-driver \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set Playwright environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user and necessary directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/uploads /ms-playwright && \
    chown -R appuser:appuser /app /ms-playwright

# Install Playwright browsers as appuser
USER appuser
RUN playwright install chromium

# Copy application code
COPY --chown=appuser:appuser . /app/

# Copy and setup entrypoint script
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/uploads /app/migrations

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health/ || exit 1

# Set entrypoint to run migrations and setup
ENTRYPOINT ["docker-entrypoint.sh"]

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "120", "--preload", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "wsgi:app"]
