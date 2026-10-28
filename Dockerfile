FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0 \
    && useradd --create-home --uid 1000 space

COPY . .

# Accounts, characters and the generated session key live in /app/instance.
RUN mkdir -p instance && chown space instance
USER space

VOLUME ["/app/instance"]
EXPOSE 5000

# One worker: with no SPACE_ONLINE_SECRET_KEY set, several workers would race to generate the key file.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "space_online.webapp:create_app()"]
