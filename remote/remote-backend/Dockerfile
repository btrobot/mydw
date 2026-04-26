ARG REMOTE_PYTHON_BASE_IMAGE=python:3.12-slim
FROM ${REMOTE_PYTHON_BASE_IMAGE}

ARG REMOTE_PIP_INDEX_URL=https://pypi.org/simple
ARG REMOTE_PIP_TRUSTED_HOST=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=${REMOTE_PIP_INDEX_URL} \
    PIP_TRUSTED_HOST=${REMOTE_PIP_TRUSTED_HOST}

WORKDIR /workspace/remote/remote-backend

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8100

ENTRYPOINT ["./scripts/start-linux.sh"]
