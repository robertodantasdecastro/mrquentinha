FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        tesseract-ocr \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/workspaces/backend

COPY workspaces/backend/requirements.txt workspaces/backend/requirements-dev.txt /tmp/requirements/
RUN pip install --no-cache-dir -r /tmp/requirements/requirements-dev.txt

COPY workspaces/backend /app/workspaces/backend
COPY docker/backend/entrypoint.sh /usr/local/bin/mrq-backend-entrypoint

RUN chmod +x /usr/local/bin/mrq-backend-entrypoint \
    && mkdir -p /app/workspaces/backend/media

ENV PYTHONPATH=/app/workspaces/backend/src \
    DJANGO_SETTINGS_MODULE=config.settings.dev

EXPOSE 8000

ENTRYPOINT ["mrq-backend-entrypoint"]
CMD ["dev"]
