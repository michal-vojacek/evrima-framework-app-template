# A website on Evrima. Built by the deploy platform (DWM) on every deploy
# from docker-compose.yml, which passes EVRIMA_VERSION from the stack's settings.
#
# Stage 1 installs Evrima (the exact tag v$EVRIMA_VERSION from GitHub) and the
# website's own libraries into a virtual environment; git is needed only here.
# Stage 2 is the runtime: no git, no compilers, an unprivileged user.

FROM python:3.13-slim AS build

ARG EVRIMA_VERSION
# Where Evrima comes from. Always a released tag in production; a test build
# may point it to a wheel or another ref (docs/deploy.md, "Test the image locally").
ARG EVRIMA_SOURCE="evrima @ git+https://github.com/michal-vojacek/evrima-framework.git@v${EVRIMA_VERSION}"

RUN test -n "$EVRIMA_VERSION" || (echo "The build argument EVRIMA_VERSION is required, e.g. 0.1.0." >&2; exit 1)
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install "$EVRIMA_SOURCE" \
    && pip install -r /tmp/requirements.txt


FROM python:3.13-slim

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    FLASK_APP=mysite \
    MEDIA_ROOT=/data/media \
    WEB_CONCURRENCY=2

# An unprivileged user (docs/framework.md, "Security baseline"); uploads live
# on a volume mounted at /data/media.
RUN useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /app /data/media \
    && chown app /data/media

COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app mysite ./mysite

USER app
EXPOSE 5000

# gthread workers (Evrima docs/framework.md, "Stack"); WEB_CONCURRENCY sets the number of
# workers. No access log here: Caddy keeps one, and the app does not need the
# visitors' IP addresses a second time.
# Worker heartbeats go to /dev/shm (memory), as the gunicorn docs advise for
# Docker: on the overlay file system they can stall a worker.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "gthread", "--threads", "4", \
     "--graceful-timeout", "20", "--worker-tmp-dir", "/dev/shm", "mysite:create_app()"]
