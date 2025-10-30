# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml ./

# Install production dependencies using uv
# Note: --system flag installs to system Python (no virtual env in container)
RUN uv pip install --system --no-cache .

# Copy application code
COPY ./app ./app

# Cloud Run will inject PORT environment variable (default 8080)
ENV PORT=8080
# Ensure Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:${PORT}/ping')"

# Run the application with uvicorn
# --host 0.0.0.0 allows external connections
# --port uses Cloud Run's PORT environment variable
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
