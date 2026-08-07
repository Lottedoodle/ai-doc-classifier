# Build from repo root:
#   docker build -t ai-document-classifier .
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app
COPY server-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server-python/ ./server-python/
RUN chown -R app:app /app

ENV PORT=3001
ENV PYTHONPATH=/app/server-python
ENV RELOAD=0

WORKDIR /app/server-python
USER app
EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3001/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
