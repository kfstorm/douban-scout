# Build stage - install dependencies
FROM ghcr.io/astral-sh/uv:python3.11-alpine AS builder

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount (excluding dev dependencies for production)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Runtime stage
FROM python:3.11-alpine AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# Copy application code
COPY app/ ./app/

# Create data directory and non-root user
RUN mkdir -p /data && \
    addgroup -S appuser -g 1000 && \
    adduser -S appuser -u 1000 -G appuser -h /data && \
    chown -R appuser:appuser /app /data

USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
