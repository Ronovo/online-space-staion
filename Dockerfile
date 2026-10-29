FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_URL=https://github.com/Ronovo/online-space-station.git \
    BUILD_CMD="pip install --no-cache-dir --user -q -r requirements.txt"

WORKDIR /app

COPY docker/git-sync.sh /usr/local/bin/git-sync
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/local/bin/git-sync

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0 \
    && useradd --create-home --uid 1000 space

COPY . .

# Accounts, characters and the generated session key live in /app/instance.
RUN mkdir -p instance && chown -R space /app
USER space

VOLUME ["/app/instance"]
EXPOSE 5000

# One worker: with no SPACE_ONLINE_SECRET_KEY set, several workers would race to generate the key file.
ENTRYPOINT ["git-sync"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "space_online.webapp:create_app()"]
