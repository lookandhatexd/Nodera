FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGEN_VORA_DB_PATH=/data/site_settings.sqlite3

WORKDIR /app

COPY Nodera.py site_settings.py ./
COPY token_docs ./token_docs

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "from urllib.request import urlopen; response = urlopen('http://127.0.0.1:8000/', timeout=3); raise SystemExit(0 if response.status == 200 else 1)"

CMD ["python", "Nodera.py", "--host", "0.0.0.0", "--port", "8000"]
