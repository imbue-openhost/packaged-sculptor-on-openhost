# Sculptor backend for OpenHost — packaged release
#
# Downloads a pre-built Sculptor AppImage from S3, extracts the
# self-contained PyInstaller binaries, and runs them directly.
#
# Build arg:
#   SCULPTOR_VERSION — release version to download (default: 0.20.0)
#                      Use "latest" to fetch the current stable release.

FROM ubuntu:24.04

ARG SCULPTOR_VERSION=0.20.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    python3 \
    supervisor \
    jq \
    vim \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (remove default ubuntu user which holds UID 1000)
RUN userdel -r ubuntu 2>/dev/null || true && \
    useradd -m -d /home/devuser -s /bin/bash -u 1000 devuser

# Download AppImage, extract sculptor_backend + sculpt CLI to /opt/sculptor.
COPY openhost/install-sculptor.sh /tmp/install-sculptor.sh
RUN chmod +x /tmp/install-sculptor.sh && /tmp/install-sculptor.sh "$SCULPTOR_VERSION" && rm /tmp/install-sculptor.sh

# Install Claude Code CLI (not auto-installed in sculptor 0.20.0).
RUN curl -fsSL https://claude.ai/install.sh | bash && \
    cp /root/.local/bin/claude /usr/local/bin/claude && \
    chmod +x /usr/local/bin/claude && \
    rm -rf /root/.claude /root/.local/bin/claude

# Setup scripts, entrypoint, and supervisord config
COPY openhost/setup/ /app/setup/
COPY openhost/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/setup/*.sh
COPY openhost/supervisord.conf /etc/supervisor/conf.d/sculptor.conf

ENV SCULPTOR_PORT=8080
ENV SCULPTOR_API_PORT=8080
ENV SCULPTOR_BIND_HOST=0.0.0.0

# Data persistence defaults (OpenHost overrides these at runtime).
ENV OPENHOST_APP_DATA_DIR=/data/app_data/sculptor
ENV OPENHOST_APP_TEMP_DIR=/data/app_temp_data/sculptor
RUN mkdir -p /data/app_data/sculptor /data/app_temp_data/sculptor && \
    chown -R devuser:devuser /data

USER root
EXPOSE 8080
CMD ["/app/entrypoint.sh"]
