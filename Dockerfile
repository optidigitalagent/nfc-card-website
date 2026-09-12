FROM node:24-bookworm-slim AS frontend
WORKDIR /app
COPY . .
ARG NFC_PUBLIC_ORIGIN
ARG NFC_PUBLICATION_MODE=PUBLIC_PREVIEW
ENV NFC_ENV=production
ENV NFC_PUBLIC_ORIGIN=${NFC_PUBLIC_ORIGIN}
ENV NFC_PUBLICATION_MODE=${NFC_PUBLICATION_MODE}
RUN npm ci && npm run build
FROM python:3.14-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV NFC_ENV=production
COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY --from=frontend /app /app
EXPOSE 8000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} server.wsgi:application"]
