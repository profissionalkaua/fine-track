FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && groupadd --gid 10001 pulso && useradd --uid 10001 --gid pulso --create-home pulso
COPY backend/ ./
RUN mkdir -p /app/.runtime/media /app/.runtime/media-work && chown -R pulso:pulso /app /ms-playwright
USER 10001:10001
CMD ["uvicorn","pulso.main:create_app","--factory","--host","0.0.0.0","--port","8000","--no-access-log"]
