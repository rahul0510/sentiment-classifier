# ── Backend Dockerfile ────────────────────────────────────────────────────────
# Multi-stage build keeps the final image lean by separating dependency
# installation from the runtime layer.

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

# Copy only requirements so Docker layer-caching skips re-install on code changes
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --prefix=/install/deps --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Copy installed packages from builder stage
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY app/ app/

# Switch to non-root user
USER appuser

# Model is downloaded at container startup (not build time).
# This keeps the build fast. The model is cached in HF_HOME after first run.

# Expose the API port
EXPOSE 8000

# Health check so Docker / Kubernetes knows when the service is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
