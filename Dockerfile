FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Most platforms set $PORT. Default to 8000 for local docker runs.
ENV PORT=8000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} app:app"]

