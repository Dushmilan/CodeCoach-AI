# syntax=docker/dockerfile:1.6
FROM python:3.11-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers wget openssl-dev libffi-dev

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level ${LOG_LEVEL:-info}