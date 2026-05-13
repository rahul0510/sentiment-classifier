# ── Frontend Dockerfile ───────────────────────────────────────────────────────

FROM python:3.11-slim

# Non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Install dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .

# Switch to non-root user
USER appuser

# Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# The BACKEND_URL env var is overridden by docker-compose to point at the
# backend service name; locally it defaults to http://localhost:8000 (see app.py)
ENV BACKEND_URL=http://backend:8000

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
