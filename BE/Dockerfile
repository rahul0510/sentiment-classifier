# ── Backend Dockerfile ────────────────────────────────────────────────────────
# Very lightweight — no PyTorch, no model weights.
# All inference is handled by HuggingFace Hosted Inference API.

FROM python:3.11-slim

RUN useradd --create-home appuser
WORKDIR /home/appuser

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY .env .env

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
