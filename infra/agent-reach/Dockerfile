# syntax=docker/dockerfile:1.7

ARG DENO_IMAGE=denoland/deno:bin-2.9.4
ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${DENO_IMAGE} AS deno_binary

FROM ${PYTHON_IMAGE} AS runtime

ARG AGENT_REACH_VERSION=1.5.0
ARG DENO_VERSION=2.9.4
ARG YTDLP_VERSION=2026.7.4
ARG YTDLP_EJS_VERSION=0.8.0
ARG PIP_VERSION=26.1.2

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/edarsa/agent-reach/venv \
    PATH=/opt/edarsa/agent-reach/venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    HOME=/var/lib/edarsa-agent-reach \
    XDG_CONFIG_HOME=/var/lib/edarsa-agent-reach/config \
    XDG_CACHE_HOME=/var/lib/edarsa-agent-reach/cache \
    DENO_DIR=/var/lib/edarsa-agent-reach/cache/deno \
    DENO_NO_UPDATE_CHECK=1 \
    DENO_NO_PROMPT=1 \
    EDARSA_AGENT_REACH_VERSION=${AGENT_REACH_VERSION} \
    EDARSA_DENO_VERSION=${DENO_VERSION} \
    EDARSA_YTDLP_VERSION=${YTDLP_VERSION} \
    EDARSA_YTDLP_EJS_VERSION=${YTDLP_EJS_VERSION}

LABEL org.opencontainers.image.title="EDARSA Agent-Reach Runtime" \
      org.opencontainers.image.description="Runtime aislado para inteligencia externa de EDARSA BOS" \
      org.opencontainers.image.vendor="EDARSA" \
      org.opencontainers.image.version="${AGENT_REACH_VERSION}" \
      mx.edarsa.agent-reach.version="${AGENT_REACH_VERSION}" \
      mx.edarsa.deno.version="${DENO_VERSION}" \
      mx.edarsa.yt-dlp.version="${YTDLP_VERSION}" \
      mx.edarsa.yt-dlp-ejs.version="${YTDLP_EJS_VERSION}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deno_binary /deno /usr/local/bin/deno

RUN groupadd --system edarsa-agent-reach \
    && useradd \
        --system \
        --gid edarsa-agent-reach \
        --create-home \
        --home-dir /var/lib/edarsa-agent-reach \
        --shell /usr/sbin/nologin \
        edarsa-agent-reach \
    && mkdir -p \
        /opt/edarsa/agent-reach/src \
        /var/lib/edarsa-agent-reach/config/yt-dlp \
        /var/lib/edarsa-agent-reach/cache/deno \
        /work \
    && chown -R \
        edarsa-agent-reach:edarsa-agent-reach \
        /var/lib/edarsa-agent-reach \
        /work

COPY infra/agent-reach/requirements.lock \
    /opt/edarsa/agent-reach/requirements.lock

COPY third_party/agent-reach \
    /opt/edarsa/agent-reach/src

RUN python -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/python" -m pip install \
        --no-cache-dir \
        "pip==${PIP_VERSION}" \
    && "$VIRTUAL_ENV/bin/python" -m pip install \
        --no-cache-dir \
        --requirement \
        /opt/edarsa/agent-reach/requirements.lock \
    && "$VIRTUAL_ENV/bin/python" -m pip install \
        --no-cache-dir \
        --no-deps \
        --no-build-isolation \
        /opt/edarsa/agent-reach/src \
    && "$VIRTUAL_ENV/bin/python" -m pip check \
    && test "$("$VIRTUAL_ENV/bin/agent-reach" version)" = \
        "Agent Reach v${AGENT_REACH_VERSION}" \
    && test "$("$VIRTUAL_ENV/bin/yt-dlp" --version)" = \
        "${YTDLP_VERSION}" \
    && test "$(deno --version | sed -n '1s/^deno //p')" = \
        "${DENO_VERSION}" \
    && ffmpeg -version >/dev/null 2>&1 \
    && ffprobe -version >/dev/null 2>&1

COPY infra/agent-reach/yt-dlp.conf \
    /var/lib/edarsa-agent-reach/config/yt-dlp/config

COPY infra/agent-reach/healthcheck.sh \
    /usr/local/bin/agent-reach-healthcheck

RUN chmod 644 \
        /var/lib/edarsa-agent-reach/config/yt-dlp/config \
    && chmod 755 \
        /usr/local/bin/agent-reach-healthcheck \
    && chown -R \
        edarsa-agent-reach:edarsa-agent-reach \
        /var/lib/edarsa-agent-reach

USER edarsa-agent-reach

WORKDIR /work

HEALTHCHECK --interval=5m --timeout=30s --start-period=20s --retries=3 \
    CMD ["/usr/local/bin/agent-reach-healthcheck"]

ENTRYPOINT ["/opt/edarsa/agent-reach/venv/bin/agent-reach"]
CMD ["doctor", "--json"]
