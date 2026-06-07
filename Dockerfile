# Multi-stage build for YouTube Bird Studio
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies in user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/inputs /app/outputs /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy Python packages from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser tools ./tools
COPY --chown=appuser:appuser web ./web
COPY --chown=appuser:appuser config ./config
COPY --chown=appuser:appuser docs ./docs
COPY --chown=appuser:appuser SETUP.md AGENTS.md ./

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8787 \
    HOST=0.0.0.0

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8787/api/health || exit 1

EXPOSE 8787

# Run application with cloud settings
CMD ["python3", "-m", "tools.youtube_healing.dashboard_server", \
     "--host", "0.0.0.0", \
     "--port", "8787", \
     "--multi-user-root", "data/users", \
     "--public-cloud"]
