FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/remote/remote-backend

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8100

ENTRYPOINT ["./scripts/start-linux.sh"]
